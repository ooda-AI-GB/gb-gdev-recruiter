from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Activity Log"])


@router.get("/activities")
def list_activities(
    partner_id: int = None,
    action: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(ActivityLog)
    if partner_id:
        query = query.filter(ActivityLog.partner_id == partner_id)
    if action:
        query = query.filter(ActivityLog.action == action)
    total = query.count()
    items = query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(a) for a in items]}


@router.get("/activities/recent")
def recent_activities(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    items = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(50).all()
    return [serialize(a) for a in items]
