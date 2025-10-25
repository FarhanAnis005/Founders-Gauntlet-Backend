# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.security.clerk import get_auth_claims
from app.db.session import db

router = APIRouter()

@router.get("/me")
async def get_current_user(claims: dict = Depends(get_auth_claims)):
    """
    A protected endpoint that retrieves the current user's data
    from the local database based on the validated Clerk token.
    """
    try:
        clerk_id = claims.get("sub")
        if not clerk_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        user = await db.user.find_unique(where={"clerkId": clerk_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found in local database")

        return user.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))