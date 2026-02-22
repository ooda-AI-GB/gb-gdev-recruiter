from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import Partner, Deal, Commission, ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Partners"])


@router.get("/partners")
def list_partners(
    status: str = None,
    country: str = None,
    source: str = None,
    has_deals: bool = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(Partner).filter(Partner.status != "inactive")
    if status:
        query = query.filter(Partner.status == status)
    if country:
        query = query.filter(Partner.country == country)
    if source:
        query = query.filter(Partner.source == source)
    if has_deals is True:
        query = query.filter(Partner.total_deals > 0)
    elif has_deals is False:
        query = query.filter(Partner.total_deals == 0)
    total = query.count()
    partners = query.order_by(Partner.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(p) for p in partners]}


@router.get("/partners/leaderboard")
def partner_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partners = (
        db.query(Partner)
        .filter(Partner.total_deals > 0, Partner.status.in_(["active", "onboarded"]))
        .order_by(Partner.total_commission_earned.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "partner_id": p.id,
            "name": p.name,
            "country": p.country,
            "deals": p.total_deals,
            "commission": float(p.total_commission_earned or 0),
        }
        for p in partners
    ]


@router.get("/partners/by-country")
def partners_by_country(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    rows = (
        db.query(Partner.country, sqlfunc.count(Partner.id))
        .filter(Partner.status != "inactive")
        .group_by(Partner.country)
        .order_by(sqlfunc.count(Partner.id).desc())
        .all()
    )
    return [{"country": r[0], "count": r[1]} for r in rows]


@router.get("/partners/{partner_id}")
def get_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    data = serialize(partner)
    data["deals"] = [serialize(d) for d in partner.deals]
    data["commissions"] = [serialize(c) for c in partner.commissions]
    return data


@router.post("/partners")
def create_partner(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    required = ["name", "email", "country"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    partner = Partner(**{k: v for k, v in body.items() if hasattr(Partner, k)})
    db.add(partner)
    db.commit()
    db.refresh(partner)
    db.add(ActivityLog(partner_id=partner.id, action="partner_created", details={"source": partner.source}))
    db.commit()
    return serialize(partner)


@router.put("/partners/{partner_id}")
def update_partner(
    partner_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    for key, val in body.items():
        if hasattr(partner, key) and key not in ("id", "created_at"):
            setattr(partner, key, val)
    db.commit()
    db.refresh(partner)
    return serialize(partner)


@router.delete("/partners/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    partner.status = "inactive"
    db.commit()
    return {"status": "ok", "message": "Partner set to inactive"}


@router.get("/partners/{partner_id}/deals")
def partner_deals(
    partner_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return [serialize(d) for d in partner.deals]


@router.get("/partners/{partner_id}/commissions")
def partner_commissions(
    partner_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return [serialize(c) for c in partner.commissions]


@router.post("/partners/{partner_id}/onboard")
def onboard_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner = db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    partner.status = "onboarded"
    partner.onboarded_at = datetime.utcnow()
    db.add(ActivityLog(partner_id=partner.id, action="onboarded", details={"country": partner.country}))
    db.commit()
    db.refresh(partner)
    return serialize(partner)
