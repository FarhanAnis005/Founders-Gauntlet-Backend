# app/api/v1/endpoints/boardroom.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.security.clerk import get_auth_claims
from app.db.session import db
from app.services.livekit_tokens import mint_token
from app.services.persona_prompts import build_persona_instructions

router = APIRouter()

class CreateSessionRequest(BaseModel):
    persona: str
    deckId: Optional[str] = None
    roomName: Optional[str] = None
    voice: Optional[str] = None  # e.g., "Puck"

@router.post("/session")
async def create_boardroom_session(body: CreateSessionRequest, claims=Depends(get_auth_claims)):
    persona = (body.persona or "").lower()
    if persona not in {"kevin","mark","lori","barbara","robert"}:
        raise HTTPException(400, detail="Unknown persona")

    owner = claims.get("sub")
    deck_analysis = None

    # Optional deck context
    if body.deckId:
        deck = await db.deck.find_unique(where={"id": body.deckId}, include={"analyses": True})
        if not deck or deck.ownerClerkId != owner:
            raise HTTPException(404, detail="Deck not found")
        if deck.status == "ready" and deck.analyses:
            latest = max(deck.analyses, key=lambda a: a.createdAt)
            deck_analysis = latest.resultJson

    # Compose instructions for the agent
    instructions = build_persona_instructions(persona=persona, analysis=deck_analysis)
    has_deck_context = deck_analysis is not None

    # Room + tokens
    room_name = body.roomName or (f"boardroom-{body.deckId}" if body.deckId else f"boardroom-persona-{persona}")
    user_token = mint_token(identity=owner, name="Founder", room_name=room_name, role="participant")

    agent_metadata = {
        "persona": persona,
        "instructions": instructions,
        "voice": body.voice or "Puck",
    }
    agent_token = mint_token(identity=f"agent-{persona}", name=f"{persona.title()} Shark", room_name=room_name, role="agent", metadata=agent_metadata)

    return {
        "roomName": room_name,
        "userToken": user_token,
        "agentToken": agent_token,       # you’ll use this to start the agent (see step 6)
        "persona": persona,
        "hasDeckContext": has_deck_context,
        "instructions": instructions,    # optional: display in UI for debugging
    }
