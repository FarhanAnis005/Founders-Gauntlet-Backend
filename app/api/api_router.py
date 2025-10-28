# app/api/api_router.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, webhooks, decks

api_router = APIRouter()
api_router.include_router(users.router,    prefix="/users",    tags=["Users"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(decks.router,  prefix="/decks",  tags=["Decks"])
