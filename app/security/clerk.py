# app/security/clerk.py
from __future__ import annotations

import os
import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from app.core.config import CLERK_SECRET_KEY, CLERK_AUTHORIZED_PARTY

bearer_scheme = HTTPBearer(auto_error=False)

if not CLERK_SECRET_KEY:
    raise RuntimeError("CLERK_SECRET_KEY not set in .env")

# Use parameter bearer_auth per SDK docs
clerk_client = Clerk(bearer_auth=CLERK_SECRET_KEY)

def get_auth_claims(
    request: Request,
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    # Build httpx.Request object for Clerk to verify
    headers = dict(request.headers)
    cookies = request.cookies
    if auth and auth.scheme.lower() == "bearer":
        headers["authorization"] = f"Bearer {auth.credentials}"

    hx_req = httpx.Request(
        method="GET",
        url="https://backend.local/authcheck",  # dummy URL for context
        headers=headers,
        cookies=cookies,
    )

    opts = AuthenticateRequestOptions(
        authorized_parties=[CLERK_AUTHORIZED_PARTY] if CLERK_AUTHORIZED_PARTY else None
    )

    try:
        state = clerk_client.authenticate_request(hx_req, opts)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

    if not getattr(state, "is_signed_in", False):
        reason = getattr(state, "reason", "invalid session")
        raise HTTPException(status_code=401, detail=f"Unauthorized: {reason}")

    payload = getattr(state, "payload", {}) or {}
    # Normalize common claims
    payload.setdefault("user_id", payload.get("sub"))
    payload.setdefault("sub", payload.get("user_id"))

    return payload
