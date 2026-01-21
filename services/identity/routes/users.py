from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from shared.dependencies import get_session, get_current_user
from shared.models import HotelUsers
from shared.schemas import HotelUserCreate, HotelUserRead
from shared.core.security import get_password_hash

router = APIRouter()

@router.get("/{user_id}", response_model=HotelUserRead)
def get_user(
    user_id: int, 
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Enforce: Can only see users from same hotel
    stmt = select(HotelUsers).where(HotelUsers.user_id == user_id)
    user = session.exec(stmt).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=403, detail="Not authorized to view users from another hotel")
        
    return user

@router.get("/me", response_model=HotelUserRead)
def get_current_user_profile(
    current_user: HotelUsers = Depends(get_current_user),
):
    return current_user

@router.post("/", response_model=HotelUserRead)
def create_user(
    user: HotelUserCreate, 
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Auto-assign to creator's hotel
    
    db_user = HotelUsers(
        hotel_id=current_user.hotel_id, # INFERRED
        username=user.username,
        password_hash=get_password_hash(user.password), # REAL HASH
        full_name=user.full_name,
        is_active=user.is_active
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
