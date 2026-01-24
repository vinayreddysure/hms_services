from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from shared.dependencies import get_session, get_current_user
from shared.models import Rooms, HotelUsers
from shared.schemas import RoomCreate, RoomRead
from shared.utils import find_available_rooms

router = APIRouter()

@router.get("/available", response_model=List[RoomRead])
def get_available_rooms(
    check_in_at: datetime,
    expected_check_out_at: datetime,
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Returns a list of rooms available for the specific dates.
    """
    if check_in_at >= expected_check_out_at:
         raise HTTPException(status_code=400, detail="Check-out must be after check-in")
         
    rooms = find_available_rooms(
        session, 
        current_user.hotel_id, 
        check_in_at, 
        expected_check_out_at
    )
    return rooms

@router.get("", response_model=List[RoomRead])
@router.get("/", response_model=List[RoomRead])
def list_rooms(
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    List all rooms for the current user's hotel.
    """
    stmt = select(Rooms).where(Rooms.hotel_id == current_user.hotel_id)
    return session.exec(stmt).all()

@router.post("", response_model=RoomRead)
@router.post("/", response_model=RoomRead)
def create_room(
    room: RoomCreate,
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Add a new room to inventory.
    """
    db_room = Rooms(
        hotel_id=current_user.hotel_id,
        room_number=room.room_number,
        room_type=room.room_type,
        rate=room.rate,
        status=room.status
    )
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room
