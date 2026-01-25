from datetime import datetime
from typing import Optional, Any, Dict, List
from decimal import Decimal
from sqlmodel import Field, SQLModel, func
from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Index, BigInteger, CheckConstraint, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

class Hotels(SQLModel, table=True):
    __tablename__ = "hotels"

    hotel_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    phone_number: Optional[str] = Field(default=None) 
    email: Optional[str] = Field(default=None)
    terms_and_conditions: str
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), default=func.now())
        )
    
    subscription_valid: bool = Field(default=False)
    valid_from: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    valid_to: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # --- New Fields for Registration & Customization ---
    layout_json: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    receipt_settings_json: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )

# --- 2. Customers ---
class Customers(SQLModel, table=True):
    __tablename__ = "customers"

    customer_id: Optional[int] = Field(default=None, primary_key=True)
    gov_id: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    phone: Optional[str] = Field(default=None)
    
    # Address Fields
    address: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    zip_code: Optional[str] = Field(default=None)
    
    average_rating: Optional[Decimal] = Field(
        default=None, 
        sa_column=Column(DECIMAL(precision=3, scale=2), nullable=True)
    )
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )

# --- 3. CustomerNotes ---
class CustomerNotes(SQLModel, table=True):
    __tablename__ = "customer_notes"
    __table_args__ = (
        Index("idx_customer_hotel", "customer_id", "hotel_id"), 
    )
    note_id: Optional[int] = Field(default=None, primary_key=True)
    note: Optional[str] = Field(default=None)
    customer_id: int = Field(foreign_key="customers.customer_id")
    hotel_id: int = Field(foreign_key="hotels.hotel_id")

# --- 4. HotelUsers ---
class HotelUsers(SQLModel, table=True):
    __tablename__ = "hotelusers"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.hotel_id")
    username: str = Field(unique=True , index=True)
    password_hash: str
    full_name: str
    is_active: bool = Field(default=True)
    
    # Password Reset
    reset_token: Optional[str] = Field(default=None, index=True)
    reset_token_expires_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

# --- 5. Rooms ---
class Rooms(SQLModel, table=True):
    __tablename__ = "rooms"
    __table_args__ = (
        Index("idx_room_hotel", "hotel_id"),
        UniqueConstraint("hotel_id", "room_number", name="uq_hotel_room_number"),
    )

    room_id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.hotel_id")
    room_number: str
    room_type: Optional[str] = Field(default=None)
    rate: Decimal = Field(sa_column=Column(DECIMAL(precision=10, scale=2)))
    status: str = Field(default="A")

# --- 6. Bookings ---
class Bookings(SQLModel, table=True):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("idx_booking_customer_hotel", "customer_id", "hotel_id"),
        Index("idx_booking_user", "created_by_user_id"),
        Index("idx_booking_hotel_date", "hotel_id", "check_in_at"),
    )

    booking_id: Optional[int] = Field(
        default=None,  
        sa_column=Column(BigInteger,primary_key=True,))
    hotel_id: int = Field(foreign_key="hotels.hotel_id")
    customer_id: int = Field(foreign_key="customers.customer_id")
    room_id: int = Field(foreign_key="rooms.room_id")
    created_by_user_id: int = Field(foreign_key="hotelusers.user_id")
    
    num_guests: int = Field(default=1)
    
    check_in_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    
    expected_check_out_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)))
    
    actual_check_out_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
    total_amount: Decimal = Field(
        sa_column=Column(DECIMAL(precision=10, scale=2)))
    cash_amount: Optional[Decimal] = Field(
        default=0, sa_column=Column(DECIMAL(precision=10, scale=2), default=0))
    card_amount: Optional[Decimal] = Field(
        default=0, sa_column=Column(DECIMAL(precision=10, scale=2), default=0))
    status: str = Field(default="Active")

# --- 7. CustomerFeedbacks ---
class CustomerFeedbacks(SQLModel, table=True):
    __tablename__ = "customerfeedbacks"
    __table_args__ = (
        Index("idx_feedback_customer", "customer_id"),
        CheckConstraint("rating >= 1 AND rating <= 10", name="chk_rating")
    )

    feedback_id: Optional[int] = Field(default=None,
                                       sa_column=Column(BigInteger, primary_key=True))
    booking_id: int = Field(sa_column=Column(BigInteger,
                                             ForeignKey("bookings.booking_id"), 
                                             unique=True,
                                             nullable=False))
    customer_id: int = Field(foreign_key="customers.customer_id")
    hotel_id: int = Field(foreign_key="hotels.hotel_id")

    rating: int = Field(sa_column=Column(SmallInteger))
    notes: Optional[str] = Field(default=None)
    
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
