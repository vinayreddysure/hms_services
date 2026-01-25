from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from shared.dependencies import get_session
from shared.models import HotelUsers, Hotels, Rooms
from shared.schemas import RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest
from shared.core.security import verify_password, create_access_token, get_password_hash
from shared.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
import secrets
import smtplib
from email.mime.text import MIMEText
import os

router = APIRouter()

@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # 1. Fetch user
    query = select(HotelUsers).where(HotelUsers.username == form_data.username)
    user = session.exec(query).first()
    
    # 2. Verify password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Create Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, # Subject is User ID
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "hotel_id": user.hotel_id}

@router.post("/register")
def register_hotel(
    payload: RegisterRequest,
    session: Session = Depends(get_session)
):
    # 1. Check if user already exists
    existing_user = session.exec(select(HotelUsers).where(HotelUsers.username == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # 1.1 Pre-validate Room Numbers in Payload
    all_room_numbers = set()
    for floor in payload.floors:
        for room in floor.rooms:
            if room.number in all_room_numbers:
                raise HTTPException(status_code=400, detail=f"Duplicate room number found in layout: {room.number}")
            all_room_numbers.add(room.number)

    # 2. Create Hotel
    layout_data = [floor.model_dump() for floor in payload.floors]
    receipt_data = payload.receiptSettings.model_dump() if payload.receiptSettings else None
    
    new_hotel = Hotels(
        name=payload.hotelName,
        address=f"{payload.streetAddress}, {payload.city}, {payload.state} {payload.zipCode}, {payload.country}",
        phone_number=payload.phone,
        email=payload.email,
        terms_and_conditions="Standard Terms Applied.",
        subscription_valid=True,
        layout_json=layout_data,
        receipt_settings_json=receipt_data
    )
    session.add(new_hotel)
    session.commit()
    session.refresh(new_hotel)
    
    # 3. Create Owner User
    hashed_password = get_password_hash(payload.password)
    new_user = HotelUsers(
        hotel_id=new_hotel.hotel_id,
        username=payload.ownerEmail, # Username is Email
        full_name=payload.ownerName,
        password_hash=hashed_password,
        is_active=True
    )
    session.add(new_user)
    
    # 4. Create Rooms (Iterate Floors -> Rooms)
    try:
        for floor in payload.floors:
            for room_data in floor.rooms:
                new_room = Rooms(
                    hotel_id=new_hotel.hotel_id,
                    room_number=room_data.number,
                    room_type=room_data.type,
                    rate=room_data.rate,
                    status="A" # Available Default
                )
                session.add(new_room)
                
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error: Possible duplicate room numbers or invalid data.")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    return {"status": "success", "hotel_id": new_hotel.hotel_id}

# --- Password Reset Endpoints ---

def send_reset_email_task(email: str, reset_link: str):
    """
    Sends email in background to prevent blocking the main request thread.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    
    email_sent = False
    if smtp_user and smtp_pass:
        try:
            msg = MIMEText(f"Click to reset your password: {reset_link}")
            msg['Subject'] = "Password Reset Request"
            msg['From'] = smtp_user
            msg['To'] = email
            
            if smtp_port == 465:
                # Use SSL
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                # Use STARTTLS (Default i.e 587)
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            email_sent = True
        except Exception as e:
            print(f"SMTP Failed: {e}")
            
    if not email_sent:
        # Fallback for Dev / No SMTP Configured
        print(f"DEV MODE: Reset Token Generated for {email}")
        print(f"DEV MODE: Link: {reset_link}")

@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    user = session.exec(select(HotelUsers).where(HotelUsers.username == payload.email)).first()
    if not user:
        # Return 200 to avoid user enumeration
        return {"message": "If email exists, reset link sent"}
    
    # Generate Token
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    # Use UTC to prevent naive vs aware comparison issues
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    session.add(user)
    session.commit()
    
    # Generate Link
    # Note: In production, this should ideally use the frontend URL from env
    # But for now localhost:3000 is hardcoded in the original logic. 
    # User can update env later.
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
    # Queue Email Task
    background_tasks.add_task(send_reset_email_task, payload.email, reset_link)
    
    return {"message": "If email exists, reset link sent"}

@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    session: Session = Depends(get_session)
):
    query = select(HotelUsers).where(HotelUsers.reset_token == payload.token)
    user = session.exec(query).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
        
    # Use UTC for comparison
    if user.reset_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")
        
    # Update Password
    user.password_hash = get_password_hash(payload.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    session.add(user)
    session.commit()
    
    return {"message": "Password reset successfully"}
