# app/api/v1/endpoints/webhooks.py
from fastapi import APIRouter, Request, HTTPException
from svix.webhooks import Webhook, WebhookVerificationError
from app.core.config import CLERK_WEBHOOK_SECRET
from app.db.session import db

router = APIRouter()

@router.post("/clerk")
async def clerk_webhook(request: Request):
    """
    Handles incoming webhooks from Clerk to sync user data with the local database.
    """
    try:
        headers = dict(request.headers)
        body = await request.body()
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        payload = wh.verify(body, headers)
        event_type = payload.get("type")
        data = payload.get("data")

        print(f"Received webhook event: {event_type}")

        if event_type == "user.created":
            email_info = data.get("email_addresses", [])
            if email_info:
                user_data = {
                    "clerkId": data.get("id"),
                    "email": email_info[0].get("email_address")
                }
                if all(user_data.values()):
                    await db.user.create(data=user_data)
                    print(f"User {user_data['clerkId']} created in database.")
        
        # Add other event types like user.deleted here if needed

        return {"status": "success", "message": f"Event '{event_type}' processed."}
    except WebhookVerificationError as e:
        raise HTTPException(status_code=400, detail="Webhook verification failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))