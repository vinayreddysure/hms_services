from sqlmodel import Session, select
from shared.models import HotelUsers
from shared.schemas import HotelUserCreate

def get_hotel_users(session: Session, hotel_id: int = None):
    statement = select(HotelUsers)
    if hotel_id:
        statement = statement.where(HotelUsers.hotel_id == hotel_id)
    return session.exec(statement).all()

def get_user_by_username(session: Session, username: str):
    statement = select(HotelUsers).where(HotelUsers.username == username)
    return session.exec(statement).first()

def create_hotel_user(session: Session, user: HotelUserCreate):
    # In a real app, hash the password here
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = HotelUsers(
        hotel_id=user.hotel_id,
        username=user.username,
        password_hash=fake_hashed_password,
        full_name=user.full_name,
        is_active=user.is_active
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
