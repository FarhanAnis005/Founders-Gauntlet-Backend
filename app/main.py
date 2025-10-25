# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_router import api_router
from app.db.session import db

# Initialize FastAPI app
app = FastAPI(title="Shark Tank AI Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App Lifespan (Connect/Disconnect Prisma)
@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        await db.disconnect()

# Include the main API router
app.include_router(api_router, prefix="/api")

# Simple root endpoint for testing
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Shark Tank AI Backend"}
