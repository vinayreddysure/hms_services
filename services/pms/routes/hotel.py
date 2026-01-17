from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from shared.dependencies import get_session
from shared.models import Hotels
from shared.schemas import HotelCreate, HotelRead

router = APIRouter()

@router.post("/", response_model=HotelRead)
def create_hotel(record: HotelCreate, session: Session = Depends(get_session)):
    db_hotel = Hotels(**record.model_dump())
    session.add(db_hotel)
    session.commit()
    session.refresh(db_hotel)
    return db_hotel

@router.get("/{hotel_id}", response_model=HotelRead)
def get_hotel(hotel_id: int, session: Session = Depends(get_session)):
    hotel = session.get(Hotels, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="hotel not found")
    return hotel