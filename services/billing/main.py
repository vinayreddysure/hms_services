import os
import stripe
from fastapi import FastAPI, Request, HTTPException, Header
from sqlmodel import Session, select
from datetime import datetime, timedelta

from shared.database import engine
from shared.models import Hotels

app = FastAPI(title="Billing Service")

# --- Logging Middleware ---
from shared.middleware import LogExceptionMiddleware
app.add_middleware(LogExceptionMiddleware)

# Env Variables
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_API_KEY

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        await handle_payment_succeeded(invoice)

    return {"status": "success"}

async def handle_payment_succeeded(invoice):
    # Assumption: We store 'hotel_id' in Stripe Customer Metadata 
    # OR we use the email to find the hotel.
    customer_id = invoice.get("customer")
    customer_email = invoice.get("customer_email")
    
    # Simple logic: Find hotel by email (if unique) or metadata
    # For this demo, let's try to extract hotel_id from metadata if present
    # In a real app, you'd fetch the Stripe Customer object to get metadata
    
    with Session(engine) as session:
        # Strategy: Find Hotel by Email first (assuming hotel email matches stripe email)
        query = select(Hotels).where(Hotels.email == customer_email)
        hotel = session.exec(query).first()
        
        if hotel:
            # Extend validity by 30 days (simplified)
            now = datetime.utcnow()
            if hotel.valid_to and hotel.valid_to > now:
                # Extend from current expiry
                new_valid_to = hotel.valid_to + timedelta(days=30)
            else:
                # Extend from now
                new_valid_to = now + timedelta(days=30)
            
            hotel.subscription_valid = True
            hotel.valid_to = new_valid_to
            session.add(hotel)
            session.commit()
            print(f"Updated subscription for Hotel {hotel.hotel_id} until {new_valid_to}")
        else:
            print(f"No hotel found for email {customer_email}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "billing"}
