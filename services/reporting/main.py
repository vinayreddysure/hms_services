from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import pandas as pd
import io
from datetime import datetime
from typing import Optional

from shared.database import engine
from shared.models import Bookings

app = FastAPI(title="Reporting Service")

# --- Logging Middleware ---
from shared.middleware import LogExceptionMiddleware
app.add_middleware(LogExceptionMiddleware)

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/reports/bookings")
def generate_booking_report(
    hotel_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: Session = Depends(get_session)
):
    # Construct Query
    query = select(Bookings).where(Bookings.hotel_id == hotel_id)
    
    if start_date:
        query = query.where(Bookings.check_in_at >= start_date)
    if end_date:
        query = query.where(Bookings.check_in_at <= end_date)
        
    # Execute (fetch all for report)
    # Warning: For massive datasets, use chunking. For MVP, fetch all is fine.
    bookings = session.exec(query).all()
    
    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for criteria")
        
    # Convert to Pandas DataFrame
    data = [b.dict() for b in bookings]
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=bookings_report.csv"
    
    return response

@app.get("/health")
def health():
    return {"status": "ok", "service": "reporting"}
