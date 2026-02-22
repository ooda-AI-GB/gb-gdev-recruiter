from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import Deal, Partner, Commission, ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Deals"])


@router.get("/deals")
def list_deals(
    partner_id: int = None,
    status: str = None,
    country: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(Deal)
    if partner_id:
        query = query.filter(Deal.partner_id == partner_id)
    if status:
        query = query.filter(Deal.status == status)
    if country:
        query = query.filter(Deal.client_country == country)
    total = query.count()
    deals = query.order_by(Deal.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(d) for d in deals]}


@router.get("/deals/{deal_id}")
def get_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    data = serialize(deal)
    data["commissions"] = [serialize(c) for c in deal.commissions]
    return data


@router.post("/deals")
def create_deal(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    required = ["partner_id", "client_name", "deal_value"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    partner = db.get(Partner, body["partner_id"])
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # Auto-calculate commission from partner's rate
    deal_value = float(body["deal_value"])
    commission_rate = float(partner.commission_rate or 0.20)
    commission_amount = body.get("commission_amount", round(deal_value * commission_rate, 2))

    deal = Deal(
        partner_id=partner.id,
        client_name=body["client_name"],
        client_email=body.get("client_email"),
        client_company=body.get("client_company"),
        client_country=body.get("client_country"),
        client_industry=body.get("client_industry"),
        deal_type=body.get("deal_type", "annual"),
        deal_value=deal_value,
        commission_amount=commission_amount,
        status=body.get("status", "prospect"),
        notes=body.get("notes"),
    )
    db.add(deal)
    db.flush()

    db.add(ActivityLog(
        partner_id=partner.id,
        action="deal_created",
        details={"deal_id": deal.id, "client": deal.client_name, "value": deal_value},
    ))
    db.commit()
    db.refresh(deal)
    return serialize(deal)


@router.put("/deals/{deal_id}")
def update_deal(
    deal_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for key, val in body.items():
        if hasattr(deal, key) and key not in ("id", "created_at"):
            setattr(deal, key, val)
    db.commit()
    db.refresh(deal)
    return serialize(deal)


@router.post("/deals/{deal_id}/close")
def close_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal.status = "closed"
    deal.closed_at = datetime.utcnow()

    # Create commission record
    commission = Commission(
        partner_id=deal.partner_id,
        deal_id=deal.id,
        amount=deal.commission_amount,
        status="pending",
    )
    db.add(commission)

    # Update partner stats
    partner = db.get(Partner, deal.partner_id)
    if partner:
        partner.total_deals = (partner.total_deals or 0) + 1
        partner.total_commission_earned = float(partner.total_commission_earned or 0) + float(deal.commission_amount)
        partner.last_active_at = datetime.utcnow()
        if not partner.first_deal_at:
            partner.first_deal_at = datetime.utcnow()
        if partner.status == "onboarded":
            partner.status = "active"

    db.add(ActivityLog(
        partner_id=deal.partner_id,
        action="deal_closed",
        details={"deal_id": deal.id, "value": float(deal.deal_value), "commission": float(deal.commission_amount)},
    ))
    db.commit()
    db.refresh(deal)
    return serialize(deal)


@router.post("/deals/{deal_id}/lost")
def lose_deal(
    deal_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.status = "lost"
    body = body or {}
    db.add(ActivityLog(
        partner_id=deal.partner_id,
        action="deal_lost",
        details={"deal_id": deal.id, "reason": body.get("reason", "")},
    ))
    db.commit()
    db.refresh(deal)
    return serialize(deal)
