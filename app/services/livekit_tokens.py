# app/services/livekit_tokens.py
import json, time, jwt
from app.core.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET

def mint_token(*, identity: str, name: str, room_name: str, role: str, metadata: dict | None = None) -> str:
    """
    Creates a LiveKit access token with a basic Video grant.
    """
    now = int(time.time())
    claims = {
        "iss": LIVEKIT_API_KEY,
        "sub": identity,
        "name": name,
        "nbf": now - 10,
        "exp": now + 60 * 60,
        "video": {
            "room": room_name,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
        },
        "metadata": json.dumps(metadata or {}),
    }
    return jwt.encode(claims, LIVEKIT_API_SECRET, algorithm="HS256")
