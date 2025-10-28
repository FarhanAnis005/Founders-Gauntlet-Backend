# app/api/v1/endpoints/decks.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.security.clerk import get_auth_claims
from app.services.storage import save_upload
from app.background.tasks import process_deck
from app.db.session import db

router = APIRouter()

@router.post("", status_code=status.HTTP_202_ACCEPTED)  # POST /api/decks
async def upload_deck(
    file: UploadFile = File(...),
    claims: dict = Depends(get_auth_claims),
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    owner = claims.get("sub")
    contents = await file.read()
    upload_path = save_upload(contents, file.filename)

    deck = await db.deck.create(
        data={
            "ownerClerkId": owner,
            "originalName": file.filename or "deck.pdf",
            "uploadPath": upload_path,
            "status": "uploaded",
        }
    )

    process_deck.delay(deck.id, upload_path)
    return {"deckId": deck.id, "status": "uploaded"}


@router.get("/{deck_id}/status")
async def get_deck_status(
    deck_id: str,
    claims: dict = Depends(get_auth_claims),
):
    owner = claims.get("sub")
    deck = await db.deck.find_unique(where={"id": deck_id})
    if not deck or deck.ownerClerkId != owner:
        raise HTTPException(status_code=404, detail="Deck not found")

    return {"deckId": deck.id, "status": deck.status, "error": deck.error}


@router.get("/{deck_id}/analysis")
async def get_deck_analysis(deck_id: str, claims: dict = Depends(get_auth_claims)):
    owner = claims.get("sub")
    deck = await db.deck.find_unique(where={"id": deck_id}, include={"analyses": True})
    if not deck or deck.ownerClerkId != owner:
        raise HTTPException(status_code=404, detail="Deck not found")

    if deck.status != "ready":
        raise HTTPException(status_code=409, detail=f"Deck not ready (status={deck.status})")

    if not deck.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    latest = max(deck.analyses, key=lambda a: a.createdAt)
    return latest.resultJson
