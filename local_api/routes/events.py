from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from typing import List

from infra.db import SessionLocal
from infra.orm_models import EventCalendarORM
from local_api.schemas import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["Seasonality"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[EventResponse])
def list_events(db: Session = Depends(get_db)):
    """List all seasonality events."""
    events = db.scalars(select(EventCalendarORM).order_by(EventCalendarORM.date)).all()
    return events

@router.post("/", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new seasonality event."""
    db_event = EventCalendarORM(
        name=event.name,
        date=event.date,
        factor=event.factor,
        applies_to=event.applies_to,
        note=event.note
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventCreate, db: Session = Depends(get_db)):
    """Update an existing event."""
    db_event = db.get(EventCalendarORM, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_event.name = event_update.name
    db_event.date = event_update.date
    db_event.factor = event_update.factor
    db_event.applies_to = event_update.applies_to
    db_event.note = event_update.note
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event."""
    db_event = db.get(EventCalendarORM, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted"}

@router.post("/backtest/seasonality")
def run_seasonality_backtest(db: Session = Depends(get_db)):
    """
    Run backtest to compare forecast accuracy with/without seasonality.
    
    TODO: Integrate with scripts/backtest_seasonality.py logic.
    For now returns a stub response.
    """
    # Placeholder response
    return {
        "status": "completed",
        "metrics_before": {"mae": 10.5, "mape": 0.15},
        "metrics_after": {"mae": 8.2, "mape": 0.11},
        "improvement_pct": 21.9,
        "details": "Backtest logic to be implemented."
    }
