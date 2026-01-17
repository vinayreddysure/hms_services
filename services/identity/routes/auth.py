from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from shared.dependencies import get_session
from shared.models import HotelUsers, Hotels, Rooms
from shared.schemas import RegisterRequest
from shared.core.security import verify_password, create_access_token, get_password_hash
from shared.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

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
    
    return {"status": "success", "hotel_id": new_hotel.hotel_id}
