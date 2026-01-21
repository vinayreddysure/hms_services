from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime, timezone
from shared.dependencies import get_session, get_current_user
from shared.models import Bookings, HotelUsers
from shared.schemas import BookingCreate, BookingRead

from shared.utils import is_room_available

router = APIRouter()

@router.post("/check-in", response_model=BookingRead)
def check_in(
    booking: BookingCreate,
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    start_time = booking.check_in_at or datetime.now(timezone.utc)
    
    # Overlap Check
    # Overlap Check
    if not is_room_available(session, booking.room_id, start_time, booking.expected_check_out_at):
        raise HTTPException(status_code=409, detail="Room is already booked/occupied for these dates")

    # Security: Verify Room Ownership
    # Ensure the room actually belongs to THIS hotel
    from shared.models import Rooms
    room = session.get(Rooms, booking.room_id)
    if not room or room.hotel_id != current_user.hotel_id:
         raise HTTPException(status_code=403, detail="Invalid Room ID: This room does not belong to your hotel.")

    # Enforce Tenant
    new_booking = Bookings(
        hotel_id=current_user.hotel_id, # INFERRED
        customer_id=booking.customer_id,
        room_id=booking.room_id,
        created_by_user_id=current_user.user_id, # INFERRED
        check_in_at=start_time,
        expected_check_out_at=booking.expected_check_out_at,
        actual_check_out_at=None,
        total_amount=booking.total_amount,
        status=booking.status
    )
    session.add(new_booking)
    session.commit()
    session.refresh(new_booking)
    return new_booking

@router.post("/check-out/{booking_id}", response_model=BookingRead)
def check_out(
    booking_id: int,
    total_amount: float,
    status: str = "Completed",
    actual_check_out_at: datetime = None,
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    stmt = select(Bookings).where(Bookings.booking_id == booking_id)
    booking = session.exec(stmt).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Enforce: Can only check out bookings from YOUR hotel
    if booking.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=403, detail="Not authorized to access bookings from another hotel")

    booking.total_amount = total_amount
    booking.status = status
    booking.actual_check_out_at = actual_check_out_at or datetime.now(timezone.utc)
    
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking