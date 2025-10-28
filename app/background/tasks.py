# app/background/tasks.py
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from typing import Any, Dict

from app.core.celery_app import celery_app
from app.services.deck_processor import analyze_pdf_doc_understanding
from prisma import Prisma

# Try to import Prisma's Json wrapper (older/newer versions differ).
try:
    from prisma import Json as PrismaJson
    def as_json(obj): return PrismaJson(obj)
except Exception:
    # fallback: many versions accept a raw dict
    def as_json(obj): return obj


def _trim(s: str, limit: int = 2000) -> str:
    s = s or ""
    return (s[: limit - 3] + "...") if len(s) > limit else s


@celery_app.task(name="app.background.tasks.process_deck", bind=True)
def process_deck(self, deck_id: str, pdf_path: str) -> Dict[str, Any]:
    """
    Celery entrypoint (sync). Runs the async Prisma flow via asyncio.run()
    because prisma-client-py is generated with interface="asyncio".
    Uses Deck (artifact) and DeckAnalysis. Persona is NOT part of the deck.
    Also applies a Windows/Celery stdio workaround so Prisma engine can spawn.
    """
    async def _run() -> Dict[str, Any]:
        # --- Windows/Celery/Prisma stdio workaround ---
        orig_stdout, orig_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        os.environ.setdefault("PRISMA_ENGINE_STDIO", "inherit")

        local = Prisma()
        try:
            await local.connect()
        finally:
            # restore Celery logging proxies after engine spawned
            sys.stdout, sys.stderr = orig_stdout, orig_stderr

        try:
            # 1) Fetch deck
            deck = await local.deck.find_unique(where={"id": deck_id})
            if not deck:
                return {"ok": False, "error": f"Deck {deck_id} not found"}

            # 2) Idempotency: if already ready, skip
            if getattr(deck, "status", None) == "ready":
                return {"ok": True, "skipped": "already_ready"}

            # 3) Mark processing
            await local.deck.update(
                where={"id": deck_id},
                data={"status": "processing", "error": None},
            )

            # 4) Run analysis (single-shot, Gemini 2.5 Pro/Flash from config)
            result_obj = analyze_pdf_doc_understanding(pdf_path)

            # 5) Persist DeckAnalysis:
            #    - Use relation connect, not FK scalar
            #    - Wrap JSON with PrismaJson if needed
            await local.deckanalysis.create(
                data={
                    "deck": {"connect": {"id": deck_id}},   
                    "resultJson": as_json(result_obj),
                }
            )

            # 6) Mark ready
            await local.deck.update(
                where={"id": deck_id},
                data={"status": "ready"},
            )

            return {"ok": True, "deck_id": deck_id}

        except Exception as exc:
            msg = f"{exc.__class__.__name__}: {str(exc)}"
            stack = traceback.format_exc()
            try:
                await local.deck.update(
                    where={"id": deck_id},
                    data={"status": "failed", "error": _trim(f"{msg}\n{stack}")},
                )
            except Exception:
                pass
            raise
        finally:
            await local.disconnect()

    return asyncio.run(_run())
