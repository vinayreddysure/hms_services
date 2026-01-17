from datetime import datetime
from sqlmodel import Session, select
from typing import List
from shared.models import Bookings, Rooms

def is_room_available(
    session: Session, 
    room_id: int, 
    check_in_at: datetime, 
    expected_check_out_at: datetime
) -> bool:
    """
    Returns True if the room is available (not booked) for the given time range.
    """
    # Overlap logic: 
    # Existing Booking [Start, End] overlaps with Request [ReqStart, ReqEnd] if:
    # ExistingStart < ReqEnd AND ExistingEnd > ReqStart
    # We only care about active bookings.
    
    query = select(Bookings).where(
        Bookings.room_id == room_id,
        Bookings.status == "Active",
        Bookings.check_in_at < expected_check_out_at,
        Bookings.expected_check_out_at > check_in_at
    )
    # If any booking is found, it's NOT available
    existing_booking = session.exec(query).first()
    return existing_booking is None

def find_available_rooms(
    session: Session,
    hotel_id: int,
    check_in_at: datetime,
    expected_check_out_at: datetime
) -> List[Rooms]:
    """
    Returns a list of Rooms for the given hotel that are available for the date range.
    """
    # 1. Get all rooms for the hotel
    all_rooms = session.exec(select(Rooms).where(Rooms.hotel_id == hotel_id)).all()
    
    # 2. Get list of booked room IDs for this range
    booked_room_ids_query = select(Bookings.room_id).where(
        Bookings.hotel_id == hotel_id,
        Bookings.status == "Active",
        Bookings.check_in_at < expected_check_out_at,
        Bookings.expected_check_out_at > check_in_at
    )
    booked_room_ids = session.exec(booked_room_ids_query).all()
    booked_set = set(booked_room_ids)
    
    # 3. Filter
    available_rooms = [r for r in all_rooms if r.room_id not in booked_set]
    return available_rooms
