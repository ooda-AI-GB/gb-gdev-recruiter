from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import JobPosting, ActivityLog

router = APIRouter(prefix="/api/v1", tags=["Job Postings"])


@router.get("/jobs")
def list_jobs(
    platform: str = None,
    status: str = None,
    country: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(JobPosting)
    if platform:
        query = query.filter(JobPosting.platform == platform)
    if status:
        query = query.filter(JobPosting.status == status)
    if country:
        query = query.filter(JobPosting.target_country == country)
    total = query.count()
    jobs = query.order_by(JobPosting.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(j) for j in jobs]}


@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return serialize(job)


@router.post("/jobs")
def create_job(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    required = ["platform", "title", "description"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    job = JobPosting(**{k: v for k, v in body.items() if hasattr(JobPosting, k)})
    db.add(job)
    db.commit()
    db.refresh(job)
    db.add(ActivityLog(action="posted_job", details={"job_id": job.id, "platform": job.platform, "title": job.title}))
    db.commit()
    return serialize(job)


@router.put("/jobs/{job_id}")
def update_job(
    job_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    for key, val in body.items():
        if hasattr(job, key) and key not in ("id", "created_at"):
            setattr(job, key, val)
    db.commit()
    db.refresh(job)
    return serialize(job)


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    db.delete(job)
    db.commit()
    return {"status": "ok"}


@router.post("/jobs/{job_id}/publish")
def publish_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    job.status = "active"
    job.posted_at = datetime.utcnow()
    db.add(ActivityLog(action="posted_job", details={"job_id": job.id, "platform": job.platform}))
    db.commit()
    db.refresh(job)
    return serialize(job)


@router.post("/jobs/{job_id}/refresh")
def refresh_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    job.refreshed_at = datetime.utcnow()
    db.add(ActivityLog(action="job_refreshed", details={"job_id": job.id}))
    db.commit()
    db.refresh(job)
    return serialize(job)


@router.post("/jobs/{job_id}/close")
def close_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    job.status = "closed"
    db.add(ActivityLog(action="job_closed", details={"job_id": job.id}))
    db.commit()
    db.refresh(job)
    return serialize(job)


@router.post("/jobs/bulk-post")
def bulk_post_jobs(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    """Create multiple job postings from a base template across platforms/languages."""
    base_title = body.get("title", "")
    base_description = body.get("description", "")
    platforms = body.get("platforms", ["upwork"])
    languages = body.get("languages", ["en"])
    budget_type = body.get("budget_type")
    budget_amount = body.get("budget_amount")
    target_country = body.get("target_country")

    created = []
    for platform in platforms:
        for language in languages:
            job = JobPosting(
                platform=platform,
                title=base_title,
                description=base_description,
                target_country=target_country,
                target_language=language,
                budget_type=budget_type,
                budget_amount=budget_amount,
                status="draft",
            )
            db.add(job)
            db.flush()
            created.append(job)
    db.commit()
    return {"created": len(created), "items": [serialize(j) for j in created]}
