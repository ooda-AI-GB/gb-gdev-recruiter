import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db, serialize
from app.models import OutreachTemplate

router = APIRouter(prefix="/api/v1", tags=["Outreach Templates"])


@router.get("/templates")
def list_templates(
    type: str = None,
    platform: str = None,
    language: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    query = db.query(OutreachTemplate)
    if type:
        query = query.filter(OutreachTemplate.type == type)
    if platform:
        query = query.filter(OutreachTemplate.platform.in_([platform, "all"]))
    if language:
        query = query.filter(OutreachTemplate.language == language)
    total = query.count()
    items = query.order_by(OutreachTemplate.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [serialize(t) for t in items]}


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    template = db.get(OutreachTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return serialize(template)


@router.post("/templates")
def create_template(
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    required = ["name", "type", "body"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    template = OutreachTemplate(**{k: v for k, v in body.items() if hasattr(OutreachTemplate, k)})
    db.add(template)
    db.commit()
    db.refresh(template)
    return serialize(template)


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    template = db.get(OutreachTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, val in body.items():
        if hasattr(template, key) and key not in ("id", "created_at"):
            setattr(template, key, val)
    db.commit()
    db.refresh(template)
    return serialize(template)


@router.post("/templates/{template_id}/render")
def render_template(
    template_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth),
):
    """Render a template with variable substitution."""
    template = db.get(OutreachTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    variables = body or {}
    rendered_body = template.body
    rendered_subject = template.subject or ""

    for key, value in variables.items():
        rendered_body = rendered_body.replace(f"{{{key}}}", str(value))
        rendered_subject = rendered_subject.replace(f"{{{key}}}", str(value))

    # Find unresolved variables
    unresolved = re.findall(r"\{(\w+)\}", rendered_body)

    return {
        "subject": rendered_subject,
        "body": rendered_body,
        "unresolved_variables": unresolved,
    }
