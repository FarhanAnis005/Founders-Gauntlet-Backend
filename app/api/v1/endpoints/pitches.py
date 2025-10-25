# app/api/v1/endpoints/pitches.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from app.security.clerk import get_auth_claims
from app.services.storage import save_upload
from app.background.tasks import process_deck
from app.db.session import db

router = APIRouter()

@router.post("", status_code=status.HTTP_202_ACCEPTED)  # POST /api/pitches
async def upload_pitch(
    persona: str = Form(...),
    file: UploadFile = File(...),
    claims: dict = Depends(get_auth_claims),
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    owner = claims.get("sub")
    contents = await file.read()
    upload_path = save_upload(contents, file.filename)

    # create pitch in 'uploaded'
    pitch = await db.pitch.create(
        data={
            "ownerClerkId": owner,
            "originalName": file.filename or "deck.pdf",
            "uploadPath": upload_path,
            "persona": persona,
            "status": "uploaded",
        }
    )

    # enqueue Celery task
    process_deck.delay(pitch.id, upload_path)

    return {"pitchId": pitch.id, "status": "uploaded"}


@router.get("/{pitch_id}/status")
async def get_pitch_status(
    pitch_id: str,
    claims: dict = Depends(get_auth_claims),
):
    owner = claims.get("sub")
    pitch = await db.pitch.find_unique(where={"id": pitch_id})
    if not pitch or pitch.ownerClerkId != owner:
        raise HTTPException(status_code=404, detail="Pitch not found")

    return {"pitchId": pitch.id, "status": pitch.status, "error": pitch.error}


# @router.get("/{pitch_id}/analysis")
# async def get_pitch_analysis(
#     pitch_id: str,
#     claims: dict = Depends(get_auth_claims),
# ):
#     owner = claims.get("sub")
#     pitch = await db.pitch.find_unique(
#         where={"id": pitch_id},
#         include={"analyses": True},
#     )
#     if not pitch or pitch.ownerClerkId != owner:
#         raise HTTPException(status_code=404, detail="Pitch not found")

#     if pitch.status != "ready":
#         raise HTTPException(status_code=409, detail=f"Pitch not ready (status={pitch.status})")

#     if not pitch.analyses:
#         raise HTTPException(status_code=404, detail="Analysis not found")

#     analysis = sorted(pitch.analyses, key=lambda a: a["createdAt"])[-1]
#     return analysis["resultJson"]

@router.get("/{pitch_id}/analysis")
async def get_pitch_analysis(pitch_id: str, claims: dict = Depends(get_auth_claims)):
    owner = claims.get("sub")
    pitch = await db.pitch.find_unique(where={"id": pitch_id}, include={"analyses": True})
    if not pitch or pitch.ownerClerkId != owner:
        raise HTTPException(status_code=404, detail="Pitch not found")

    if pitch.status != "ready":
        raise HTTPException(status_code=409, detail=f"Pitch not ready (status={pitch.status})")

    if not pitch.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Each item in pitch.analyses is a DeckAnalysis object (use dot attrs)
    latest = max(pitch.analyses, key=lambda a: a.createdAt)
    return latest.resultJson