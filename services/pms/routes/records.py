from typing import List, Tuple, Any, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, SQLModel
from shared.dependencies import get_session, get_current_user
from shared.models import Bookings, CustomerFeedbacks, HotelUsers, Rooms, Customers, CustomerNotes
from shared.schemas import BookingCreate, BookingRead
from shared.utils import is_room_available

router = APIRouter()

@router.get("/customers/lookup")
def lookup_customer(
    gov_id: str,
    session: Session = Depends(get_session),
    current_user: HotelUsers = Depends(get_current_user)
):
    """
    Search for a customer by Government ID (Capitalized).
    Returns customer details and basic stats if found.
    """
    if not gov_id:
        return None
        
    # Standardize ID
    search_id = gov_id.strip().upper()
    
    # 1. Find Customer
    customer = session.exec(select(Customers).where(Customers.gov_id == search_id)).first()
    
    if not customer:
        return None
        
    # 2. Key Stats
    stay_count = session.exec(select(func.count(Bookings.booking_id)).where(Bookings.customer_id == customer.customer_id)).one()
    
    last_stay = session.exec(
        select(Bookings)
        .where(Bookings.customer_id == customer.customer_id)
        .order_by(Bookings.check_in_at.desc())
    ).first()
    
    return {
        "customer_id": customer.customer_id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "phone": customer.phone,
        "gov_id": customer.gov_id,
        "insights": {
            "previousStays": stay_count,
            "lastVisit": last_stay.check_in_at if last_stay else None,
            "globalRating": float(customer.average_rating) if customer.average_rating else 5.0,
            "guestStatus": "returning" if stay_count > 0 else "new"
        }
    }

@router.post("/", response_model=BookingRead)
def create_booking(
    booking: BookingCreate,
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # --- 1. Smart ID Resolution for Rooms ---
    real_room = session.get(Rooms, booking.room_id)
    if not real_room:
        statement = select(Rooms).where(Rooms.room_number == str(booking.room_id))
        real_room = session.exec(statement).first()
        if real_room:
             booking.room_id = real_room.room_id
        else:
             raise HTTPException(status_code=404, detail=f"Room identifier {booking.room_id} not found.")

    # --- 2. Smart Customer Upsert ---
    # If no customer_id provided, look up or create based on Guest Details
    if not booking.customer_id:
        if not booking.guest_gov_id or not booking.guest_name:
             raise HTTPException(status_code=400, detail="Either customer_id or guest details (Name, ID) are required.")
        
        # Standardize
        gov_id_clean = booking.guest_gov_id.strip().upper()
        
        # Check Existing
        existing_customer = session.exec(select(Customers).where(Customers.gov_id == gov_id_clean)).first()
        
        if existing_customer:
            booking.customer_id = existing_customer.customer_id
            # Optional: Update phone if new one provided? Let's skip updating for now to be safe.
        else:
            # Create New Customer
            # Split name safely
            parts = booking.guest_name.strip().split(" ", 1)
            f_name = parts[0]
            l_name = parts[1] if len(parts) > 1 else ""
            
            new_customer = Customers(
                gov_id=gov_id_clean,
                first_name=f_name,
                last_name=l_name,
                phone=booking.guest_phone,
                average_rating=5.0
            )
            session.add(new_customer)
            session.commit()
            session.refresh(new_customer)
            booking.customer_id = new_customer.customer_id

    # --- 3. Overlap Check ---
    if booking.check_in_at and booking.expected_check_out_at:
        start_time = booking.check_in_at
        if not is_room_available(session, booking.room_id, start_time, booking.expected_check_out_at):
            raise HTTPException(status_code=409, detail="Room is already booked for these dates")

    # --- 4. Create Booking ---
    new_booking = Bookings(
        hotel_id=current_user.hotel_id,
        customer_id=booking.customer_id,
        room_id=booking.room_id,
        created_by_user_id=current_user.user_id,
        check_in_at=booking.check_in_at,
        expected_check_out_at=booking.expected_check_out_at,
        actual_check_out_at=None,
        total_amount=booking.total_amount,
        status=booking.status or "Active"
    )
    session.add(new_booking)
    session.commit()
    session.refresh(new_booking)
    return new_booking

@router.get("/customer/{customer_id}")
def get_customer_history(
    customer_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: HotelUsers = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    target_hotel_id = current_user.hotel_id
    
    # 1) My Hotel Bookings
    query = (
        select(Bookings)
        .where(Bookings.customer_id == customer_id)
        .where(Bookings.hotel_id == target_hotel_id)
        .order_by(Bookings.booking_id.desc())
        .offset(offset)
        .limit(limit)
    )
    bookings = session.exec(query).all()
    
    # 2) Global Reputation
    avg_rating_query = (
        select(func.avg(CustomerFeedbacks.rating))
        .where(CustomerFeedbacks.customer_id == customer_id)
    )
    scalar_avg = session.exec(avg_rating_query).one()
    customer_global_rating = float(scalar_avg) if scalar_avg is not None else 0.0
    
    # 3) Global Feedback
    feedback_query = (
        select(CustomerFeedbacks)
        .where(CustomerFeedbacks.customer_id == customer_id)
        .order_by(CustomerFeedbacks.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    feedbacks = session.exec(feedback_query).all()

    # 4) Visit Counts
    global_stays_query = select(func.count(Bookings.booking_id)).where(Bookings.customer_id == customer_id)
    global_stays = session.exec(global_stays_query).one()
    
    local_stays_query = (
        select(func.count(Bookings.booking_id))
        .where(Bookings.customer_id == customer_id)
        .where(Bookings.hotel_id == target_hotel_id)
    )
    local_stays = session.exec(local_stays_query).one()

    return {
        "viewer_hotel_id": target_hotel_id,
        "insights": {
            "global_rating": customer_global_rating,
            "total_system_stays": global_stays,
            "stays_at_this_hotel": local_stays
        },
        "bookings_history": bookings,
        "global_feedbacks": feedbacks
    }

class CheckoutRequest(SQLModel):
    notes: Optional[str] = None
    rating: Optional[int] = None

@router.get("/room/{room_id}/current")
def get_current_booking_for_room(
    room_id: int,
    session: Session = Depends(get_session),
    current_user: HotelUsers = Depends(get_current_user),
):
    """
    Get the currently active booking for a specific room.
    Used by the Check-Out modal to show guest details.
    """
    # Auto-resolve Room ID vs Room Number
    real_room = session.get(Rooms, room_id)
    if not real_room:
        real_room = session.exec(select(Rooms).where(Rooms.room_number == str(room_id))).first()
    
    if not real_room:
        raise HTTPException(status_code=404, detail="Room not found")

    target_room_id = real_room.room_id

    # Find active booking for this room
    statement = (
        select(Bookings)
        .where(Bookings.room_id == target_room_id)
        .where(Bookings.status == "Active")
        .order_by(Bookings.check_in_at.desc())
    )
    booking = session.exec(statement).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="No active booking found for this room")
        
    # Get Customer Details
    customer = session.get(Customers, booking.customer_id)
    
    return {
        "booking_id": booking.booking_id,
        "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "Unknown Guest",
        "customer_phone": customer.phone if customer else "",
        "check_in_at": booking.check_in_at,
        "expected_check_out_at": booking.expected_check_out_at,
        "total_amount": booking.total_amount,
        "status": booking.status
    }

@router.post("/room/{room_id}/checkout")
def checkout_room(
    room_id: int,
    request: CheckoutRequest,
    session: Session = Depends(get_session),
    current_user: HotelUsers = Depends(get_current_user),
):
    """
    Complete the check-out process for a room.
    1. Mark booking as Completed.
    2. Set Room status to Available (or Dirty).
    3. (Optional) Create feedback.
    """
    # Auto-resolve Room ID vs Room Number
    real_room = session.get(Rooms, room_id)
    if not real_room:
        real_room = session.exec(select(Rooms).where(Rooms.room_number == str(room_id))).first()
    
    if not real_room:
         raise HTTPException(status_code=404, detail="Room not found")
         
    target_room_id = real_room.room_id

    # 1. Get Active Booking
    statement = (
        select(Bookings)
        .where(Bookings.room_id == target_room_id)
        .where(Bookings.status == "Active")
        .order_by(Bookings.check_in_at.desc())
    )
    booking = session.exec(statement).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="No active booking to check out")
        
    # 2. Update Booking
    booking.status = "Completed"
    booking.actual_check_out_at = datetime.utcnow()
    session.add(booking)
    
    # 3. Update Room Status
    real_room.status = "A" # Available
    session.add(real_room)
        
    # 4. Create Feedback (if rating provided)
    if request.rating and booking.customer_id:
        feedback = CustomerFeedbacks(
            hotel_id=current_user.hotel_id,
            customer_id=booking.customer_id,
            booking_id=booking.booking_id,
            rating=request.rating,
            notes=request.notes or "",
            created_at=datetime.utcnow()
        )
        session.add(feedback)
        
    session.commit()
    
    return {"success": True, "message": "Check-out completed successfully"}

