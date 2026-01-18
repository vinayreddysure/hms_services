from typing import Optional, List, Any
from datetime import datetime
from sqlmodel import SQLModel

# --- Base Models ---
class HotelBase(SQLModel):
    name: str
    address: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    subscription_valid: bool = False
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

class BookingBase(SQLModel):
    room_id: int
    customer_id: int
    check_in_at: datetime
    expected_check_out_at: datetime
    status: str

# --- Create Models ---
class HotelCreate(HotelBase):
    pass

class BookingCreate(BookingBase):
    customer_id: Optional[int] = None
    total_amount: float
    notes: Optional[str] = None
    # Guest Upsert Fields
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_gov_id: Optional[str] = None
    # Address Upsert Fields
    guest_address: Optional[str] = None
    guest_city: Optional[str] = None
    guest_state: Optional[str] = None
    guest_zip_code: Optional[str] = None

class RoomCreate(SQLModel):
    room_number: str
    room_type: str
    rate: float
    status: str = "A"

# --- User Models (Restored) ---
class HotelUserCreate(SQLModel):
    username: str
    password: str
    full_name: str
    is_active: bool = True

class HotelUserRead(SQLModel):
    user_id: int
    hotel_id: int
    username: str
    full_name: str
    is_active: bool

class Token(SQLModel):
    access_token: str
    token_type: str
    hotel_id: int

class TokenData(SQLModel):
    username: Optional[str] = None

# --- Read Models ---
class RoomRead(RoomCreate):
    room_id: int
    hotel_id: int
    
class BookingRead(BookingBase):
    booking_id: int
    actual_check_out_at: Optional[datetime] = None
    total_amount: float

class HotelRead(HotelBase):
    hotel_id: int
    phone_number: Optional[str] = None
    email: Optional[str] = None
    layout_json: Optional[Any] = None
    receipt_settings_json: Optional[Any] = None

# --- Complex Request Models (for Registration) ---
class RoomLayout(SQLModel):
    id: str
    number: str
    type: str
    rate: float
    x: int
    y: int
    width: int
    height: int

class FloorLayout(SQLModel):
    id: str
    name: str
    rooms: List[RoomLayout]

class ReceiptSettings(SQLModel):
    businessName: str = "My Hotel"
    address: str = ""
    headerText: str = "Booking Receipt"
    footerText: str = ""
    accentColor: str = "#000000"
    showTaxId: bool = False
    taxId: str = ""
    terms: str = "Terms and Conditions..."
    showSignature: bool = True

class RegisterRequest(SQLModel):
    # Hotel Details
    hotelName: str
    email: str
    phone: str
    streetAddress: str
    city: str
    state: str
    zipCode: str
    country: str
    
    # Owner Details
    ownerName: str
    ownerEmail: str
    password: str
    
    # Layout Data
    floors: List[FloorLayout]
    
    # Receipt Settings
    receiptSettings: Optional[ReceiptSettings] = None
