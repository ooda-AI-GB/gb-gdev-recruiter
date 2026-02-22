from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import Application, Partner, JobPosting, ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Applications"])


@router.get("/applications")
def list_applications(
    status: str = None,
    platform: str = None,
    country: str = None,
    job_posting_id: int = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(Application)
    if status:
        query = query.filter(Application.status == status)
    if platform:
        query = query.filter(Application.platform == platform)
    if country:
        query = query.filter(Application.applicant_country == country)
    if job_posting_id:
        query = query.filter(Application.job_posting_id == job_posting_id)
    total = query.count()
    apps = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(a) for a in apps]}


@router.get("/applications/{app_id}")
def get_application(
    app_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize(application)


@router.post("/applications")
def create_application(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    required = ["platform", "applicant_name"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    application = Application(**{k: v for k, v in body.items() if hasattr(Application, k)})
    db.add(application)
    db.flush()

    # Increment applications_count on the job posting
    if application.job_posting_id:
        job = db.get(JobPosting, application.job_posting_id)
        if job:
            job.applications_count = (job.applications_count or 0) + 1

    db.add(ActivityLog(
        action="received_application",
        details={
            "application_id": application.id,
            "name": application.applicant_name,
            "platform": application.platform,
        },
    ))
    db.commit()
    db.refresh(application)
    return serialize(application)


@router.put("/applications/{app_id}")
def update_application(
    app_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    for key, val in body.items():
        if hasattr(application, key) and key not in ("id", "created_at"):
            setattr(application, key, val)
    db.commit()
    db.refresh(application)
    return serialize(application)


@router.post("/applications/{app_id}/auto-respond")
def auto_respond(
    app_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.auto_response_sent = True
    db.add(ActivityLog(
        partner_id=application.partner_id,
        action="sent_response",
        details={"application_id": application.id, "type": "auto_response"},
    ))
    db.commit()
    db.refresh(application)
    return serialize(application)


@router.post("/applications/{app_id}/screen")
def screen_application(
    app_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = "screened"
    application.screened_at = datetime.utcnow()
    db.add(ActivityLog(
        action="screened",
        details={"application_id": application.id, "name": application.applicant_name},
    ))
    db.commit()
    db.refresh(application)
    return serialize(application)


@router.post("/applications/{app_id}/accept")
def accept_application(
    app_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.status == "accepted":
        raise HTTPException(status_code=400, detail="Application already accepted")

    body = body or {}
    # Create partner from application
    partner = Partner(
        name=application.applicant_name,
        email=application.applicant_email or f"partner-{application.id}@pending.local",
        country=application.applicant_country or "XX",
        source=application.platform,
        source_id=application.platform_applicant_id,
        status="screening",
        commission_rate=body.get("commission_rate", 0.20),
        territory=body.get("territory", []),
    )
    db.add(partner)
    db.flush()

    application.status = "accepted"
    application.partner_id = partner.id

    db.add(ActivityLog(
        partner_id=partner.id,
        action="partner_created",
        details={"from_application": application.id, "source": application.platform},
    ))
    db.commit()
    db.refresh(partner)
    return {"application": serialize(application), "partner": serialize(partner)}


@router.post("/applications/{app_id}/reject")
def reject_application(
    app_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    application = db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = "rejected"
    body = body or {}
    db.add(ActivityLog(
        action="rejected_application",
        details={"application_id": application.id, "reason": body.get("reason", "")},
    ))
    db.commit()
    db.refresh(application)
    return serialize(application)
