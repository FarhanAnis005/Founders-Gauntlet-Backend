# app/services/deck_processor.py
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import List, Optional

import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from app.core.config import GOOGLE_API_KEY, GEMINI_MODEL


# ========= Structured Output Schema (Pydantic; no open-ended dicts) =========

class EvidenceItem(BaseModel):
    topic: str = ""
    pages: List[int] = Field(default_factory=list, description="1-based slide numbers if known")

class QuestionsByShark(BaseModel):
    kevin: List[str] = Field(default_factory=list)
    mark: List[str] = Field(default_factory=list)
    lori: List[str] = Field(default_factory=list)
    barbara: List[str] = Field(default_factory=list)
    robert: List[str] = Field(default_factory=list)

class Meta(BaseModel):
    model_used: str = ""
    pages_count: int = 0
    processed_at: str = ""      # ISO-8601
    schema_version: str = "1.0.0"

class AnalysisSchema(BaseModel):
    one_liner: str = ""
    themes: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    questions_by_shark: QuestionsByShark = Field(default_factory=QuestionsByShark)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    meta: Meta = Field(default_factory=Meta)


# ========= Prompt (unchanged) =========

PROMPT = """
You are analyzing a startup pitch deck PDF. Return STRICT JSON and nothing else.

SCHEMA (all fields REQUIRED; use empty values [] or "" where unknown):
{
  "one_liner": string,
  "themes": [string],           // 3-6 key themes
  "strengths": [string],        // 3-7, concise, include metrics if present (e.g., GM%, growth %)
  "risks": [string],            // 3-7, concise, include metrics if present
  "questions_by_shark": {
    "kevin":   [string],        // 5-10 questions focused on unit economics, margins, CAC/LTV, valuation, deal terms
    "mark":    [string],        // tech defensibility, scalability, product strategy, data moats
    "lori":    [string],        // consumer appeal, packaging, channels (retail/QVC), IP
    "barbara": [string],        // brand, storytelling, founder grit, scrappiness, sales tactics
    "robert":  [string]         // competition, B2B pipeline, cybersecurity, pricing, enterprise readiness
  },
  "evidence": [
    { "topic": string, "pages": [number] }   // optional grounding; 1-based page numbers
  ],
  "meta": {
    "model_used": string,
    "pages_count": number,
    "processed_at": string,     // ISO-8601
    "schema_version": "1.0.0"
  }
}

RULES:
- Use ONLY the provided PDF (text + visuals).
- Keep each bullet short and actionable.
- If a fact is uncertain, convert it to a clarifying question.
- If slide numbers can be inferred, include them in "evidence"; otherwise leave empty.
- Output must be valid JSON; no markdown, no prose, no code fences.
""".strip()


# ========= Processor (single-shot document understanding with structured output) =========

def analyze_pdf_doc_understanding(
    pdf_path: str,
    model_name: Optional[str] = None,
):
    """
    Single-shot document understanding: send the entire PDF to Gemini (2.5 Pro by default),
    using structured output to force strict JSON matching AnalysisSchema.
    Returns a Python dict safe to store in DeckAnalysis.resultJson.
    """
    model_to_use = model_name or GEMINI_MODEL or "gemini-2.5-pro"

    # Inline PDF bytes (limit ~20MB for inline)
    path = pathlib.Path(pdf_path)
    pdf_bytes = path.read_bytes()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise ValueError("PDF exceeds ~20MB inline limit. Use Files API or page-wise fallback.")

    # Page count for meta
    try:
        with fitz.open(pdf_path) as doc:
            pages_count = doc.page_count
    except Exception:
        pages_count = 0

    client = genai.Client(api_key=GOOGLE_API_KEY)

    contents = [
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        PROMPT,
    ]

    config = {
        "response_mime_type": "application/json",
        "response_schema": AnalysisSchema,  # Pydantic → structured output schema
        "temperature": 0.2,
    }

    resp = client.models.generate_content(
        model=model_to_use,
        contents=contents,
        config=config,
    )

    # Prefer parsed if available; otherwise parse resp.text
    if getattr(resp, "parsed", None):
        # resp.parsed is a Pydantic model (AnalysisSchema)
        data = resp.parsed.model_dump()
    else:
        text = (resp.text or "").strip()
        cleaned = text.strip("`").lstrip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
        data = json.loads(cleaned) if cleaned else {}

    # Patch meta with deterministic values
    data.setdefault("meta", {})
    data["meta"]["model_used"] = model_to_use
    data["meta"]["pages_count"] = pages_count
    data["meta"]["processed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["meta"]["schema_version"] = "1.0.0"

    return data
# todo: add a retry function n handle errors gracefully
# verify if the json is valid else retry