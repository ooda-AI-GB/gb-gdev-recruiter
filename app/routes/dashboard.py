from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db
from app.models import Partner, JobPosting, Application, Deal, Commission

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Partners
    total_partners = db.query(Partner).filter(Partner.status != "inactive").count()
    partner_by_status = dict(
        db.query(Partner.status, sqlfunc.count(Partner.id))
        .filter(Partner.status != "inactive")
        .group_by(Partner.status)
        .all()
    )
    partner_by_country = dict(
        db.query(Partner.country, sqlfunc.count(Partner.id))
        .filter(Partner.status != "inactive")
        .group_by(Partner.country)
        .order_by(sqlfunc.count(Partner.id).desc())
        .all()
    )
    new_partners_week = (
        db.query(Partner)
        .filter(Partner.created_at >= week_ago, Partner.status != "inactive")
        .count()
    )

    # Job Postings
    active_jobs = db.query(JobPosting).filter(JobPosting.status == "active").count()
    jobs_by_platform = dict(
        db.query(JobPosting.platform, sqlfunc.count(JobPosting.id))
        .filter(JobPosting.status == "active")
        .group_by(JobPosting.platform)
        .all()
    )

    # Applications
    total_apps = db.query(Application).count()
    apps_this_week = db.query(Application).filter(Application.created_at >= week_ago).count()
    apps_by_status = dict(
        db.query(Application.status, sqlfunc.count(Application.id))
        .group_by(Application.status)
        .all()
    )

    # Deals
    deal_pipeline = dict(
        db.query(Deal.status, sqlfunc.count(Deal.id))
        .group_by(Deal.status)
        .all()
    )
    total_closed_value = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(Deal.deal_value), 0))
        .filter(Deal.status == "closed")
        .scalar()
    )
    deals_this_month = db.query(Deal).filter(Deal.created_at >= month_ago).count()

    # Commissions
    total_earned = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0)).scalar()
    )
    pending_commission = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0))
        .filter(Commission.status == "pending")
        .scalar()
    )
    paid_commission = float(
        db.query(sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0))
        .filter(Commission.status == "paid")
        .scalar()
    )

    # Leaderboard
    top_partners = (
        db.query(Partner)
        .filter(Partner.total_deals > 0)
        .order_by(Partner.total_commission_earned.desc())
        .limit(10)
        .all()
    )
    leaderboard = [
        {
            "partner_id": p.id,
            "name": p.name,
            "country": p.country,
            "deals": p.total_deals,
            "commission": float(p.total_commission_earned or 0),
        }
        for p in top_partners
    ]

    # Funnel
    screened = db.query(Application).filter(Application.status.in_(["screened", "accepted"])).count()
    onboarded = db.query(Partner).filter(Partner.status.in_(["onboarded", "active"])).count()
    first_deal = db.query(Partner).filter(Partner.first_deal_at.isnot(None)).count()
    funnel_rate = f"{(first_deal / total_apps * 100):.1f}%" if total_apps > 0 else "0.0%"

    return {
        "partners": {
            "total": total_partners,
            "by_status": partner_by_status,
            "by_country": partner_by_country,
            "new_this_week": new_partners_week,
        },
        "job_postings": {
            "active": active_jobs,
            "by_platform": jobs_by_platform,
        },
        "applications": {
            "total": total_apps,
            "this_week": apps_this_week,
            "by_status": apps_by_status,
        },
        "deals": {
            "pipeline": deal_pipeline,
            "total_value_closed": total_closed_value,
            "this_month": deals_this_month,
        },
        "commissions": {
            "total_earned": total_earned,
            "pending": pending_commission,
            "paid": paid_commission,
        },
        "leaderboard": leaderboard,
        "funnel": {
            "postings": active_jobs,
            "applications": total_apps,
            "screened": screened,
            "onboarded": onboarded,
            "first_deal": first_deal,
            "conversion_rate": funnel_rate,
        },
    }
