from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc, extract
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import Commission, ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Commissions"])


@router.get("/commissions")
def list_commissions(
    partner_id: int = None,
    status: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(Commission)
    if partner_id:
        query = query.filter(Commission.partner_id == partner_id)
    if status:
        query = query.filter(Commission.status == status)
    total = query.count()
    items = query.order_by(Commission.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(c) for c in items]}


@router.get("/commissions/summary")
def commission_summary(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    pending = db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0)).filter(Commission.status == "pending").scalar()
    approved = db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0)).filter(Commission.status == "approved").scalar()
    paid = db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0)).filter(Commission.status == "paid").scalar()
    held = db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0)).filter(Commission.status == "held").scalar()
    return {
        "pending": float(pending),
        "approved": float(approved),
        "paid": float(paid),
        "held": float(held),
        "total": float(pending + approved + paid + held),
    }


@router.get("/commissions/{commission_id}")
def get_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    commission = db.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    return serialize(commission)


@router.post("/commissions/{commission_id}/approve")
def approve_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    commission = db.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    commission.status = "approved"
    db.add(ActivityLog(
        partner_id=commission.partner_id,
        action="commission_approved",
        details={"commission_id": commission.id, "amount": float(commission.amount)},
    ))
    db.commit()
    db.refresh(commission)
    return serialize(commission)


@router.post("/commissions/{commission_id}/hold")
def hold_commission(
    commission_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    commission = db.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    body = body or {}
    commission.status = "held"
    commission.held_reason = body.get("reason", "")
    db.add(ActivityLog(
        partner_id=commission.partner_id,
        action="commission_held",
        details={"commission_id": commission.id, "reason": commission.held_reason},
    ))
    db.commit()
    db.refresh(commission)
    return serialize(commission)


@router.post("/commissions/{commission_id}/mark-paid")
def mark_paid(
    commission_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    commission = db.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    body = body or {}
    commission.status = "paid"
    commission.paid_at = datetime.utcnow()
    commission.payment_method = body.get("payment_method")
    commission.payment_reference = body.get("payment_reference")
    db.add(ActivityLog(
        partner_id=commission.partner_id,
        action="commission_paid",
        details={
            "commission_id": commission.id,
            "amount": float(commission.amount),
            "method": commission.payment_method,
        },
    ))
    db.commit()
    db.refresh(commission)
    return serialize(commission)
