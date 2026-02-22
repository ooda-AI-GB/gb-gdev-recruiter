from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sqlfunc, extract, case
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db
from app.models import Partner, Application, Deal, Commission, JobPosting

router = APIRouter(prefix="/api/v1", tags=["Analytics"])


@router.get("/analytics/funnel")
def analytics_funnel(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    total_postings = db.query(JobPosting).filter(JobPosting.status == "active").count()
    total_applications = db.query(Application).count()
    screened = db.query(Application).filter(Application.status.in_(["screened", "accepted"])).count()
    accepted = db.query(Application).filter(Application.status == "accepted").count()
    onboarded = db.query(Partner).filter(Partner.status.in_(["onboarded", "active"])).count()
    active = db.query(Partner).filter(Partner.status == "active").count()
    with_deals = db.query(Partner).filter(Partner.first_deal_at.isnot(None)).count()

    def rate(num, denom):
        return f"{(num / denom * 100):.1f}%" if denom > 0 else "0.0%"

    return {
        "stages": [
            {"stage": "Job Postings", "count": total_postings},
            {"stage": "Applications", "count": total_applications},
            {"stage": "Screened", "count": screened, "rate": rate(screened, total_applications)},
            {"stage": "Accepted", "count": accepted, "rate": rate(accepted, total_applications)},
            {"stage": "Onboarded", "count": onboarded, "rate": rate(onboarded, accepted)},
            {"stage": "Active", "count": active, "rate": rate(active, onboarded)},
            {"stage": "First Deal", "count": with_deals, "rate": rate(with_deals, onboarded)},
        ],
        "overall_conversion": rate(with_deals, total_applications),
    }


@router.get("/analytics/by-country")
def analytics_by_country(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    partner_counts = dict(
        db.query(Partner.country, sqlfunc.count(Partner.id))
        .filter(Partner.status != "inactive")
        .group_by(Partner.country)
        .all()
    )
    deal_counts = dict(
        db.query(Deal.client_country, sqlfunc.count(Deal.id))
        .filter(Deal.client_country.isnot(None))
        .group_by(Deal.client_country)
        .all()
    )
    commission_sums = dict(
        db.query(
            Partner.country,
            sqlfunc.coalesce(sqlfunc.sum(Commission.amount), 0),
        )
        .join(Commission, Commission.partner_id == Partner.id)
        .group_by(Partner.country)
        .all()
    )

    countries = set(list(partner_counts.keys()) + list(deal_counts.keys()))
    result = []
    for c in sorted(countries):
        result.append({
            "country": c,
            "partners": partner_counts.get(c, 0),
            "deals": deal_counts.get(c, 0),
            "commission": float(commission_sums.get(c, 0)),
        })
    return result


@router.get("/analytics/by-platform")
def analytics_by_platform(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    app_counts = dict(
        db.query(Application.platform, sqlfunc.count(Application.id))
        .group_by(Application.platform)
        .all()
    )
    accepted_counts = dict(
        db.query(Application.platform, sqlfunc.count(Application.id))
        .filter(Application.status == "accepted")
        .group_by(Application.platform)
        .all()
    )
    partner_source_counts = dict(
        db.query(Partner.source, sqlfunc.count(Partner.id))
        .filter(Partner.source.isnot(None), Partner.status != "inactive")
        .group_by(Partner.source)
        .all()
    )
    deal_by_source = dict(
        db.query(Partner.source, sqlfunc.count(Deal.id))
        .join(Deal, Deal.partner_id == Partner.id)
        .filter(Partner.source.isnot(None))
        .group_by(Partner.source)
        .all()
    )

    platforms = set(list(app_counts.keys()) + list(partner_source_counts.keys()))
    result = []
    for p in sorted(platforms):
        total = app_counts.get(p, 0)
        accepted = accepted_counts.get(p, 0)
        result.append({
            "platform": p,
            "applications": total,
            "accepted": accepted,
            "acceptance_rate": f"{(accepted / total * 100):.1f}%" if total > 0 else "0.0%",
            "active_partners": partner_source_counts.get(p, 0),
            "deals": deal_by_source.get(p, 0),
        })
    return result


@router.get("/analytics/by-month")
def analytics_by_month(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    now = datetime.utcnow()
    result = []
    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        if i > 0:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
        else:
            next_month = now

        new_partners = (
            db.query(Partner)
            .filter(Partner.created_at >= month_start, Partner.created_at < next_month)
            .count()
        )
        new_apps = (
            db.query(Application)
            .filter(Application.created_at >= month_start, Application.created_at < next_month)
            .count()
        )
        new_deals = (
            db.query(Deal)
            .filter(Deal.created_at >= month_start, Deal.created_at < next_month)
            .count()
        )
        deal_value = float(
            db.query(sqlfunc.coalesce(sqlfunc.sum(Deal.deal_value), 0))
            .filter(Deal.status == "closed", Deal.closed_at >= month_start, Deal.closed_at < next_month)
            .scalar()
        )

        result.append({
            "month": month_start.strftime("%Y-%m"),
            "new_partners": new_partners,
            "applications": new_apps,
            "deals": new_deals,
            "closed_value": deal_value,
        })
    return result
