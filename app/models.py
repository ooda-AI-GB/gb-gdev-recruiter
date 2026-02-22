from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric,
    DateTime, Date, ForeignKey, JSON, func
)
from sqlalchemy.orm import relationship

from app.database import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    whatsapp = Column(String(50))
    country = Column(String(3), nullable=False)
    city = Column(String(100))
    languages = Column(JSON, default=["en"])
    background = Column(String(50))
    network_description = Column(Text)
    status = Column(String(20), default="applied")
    source = Column(String(20))
    source_id = Column(String(255))
    referrer_id = Column(Integer, ForeignKey("partners.id"))
    territory = Column(JSON, default=[])
    commission_rate = Column(Numeric(3, 2), default=0.20)
    total_deals = Column(Integer, default=0)
    total_commission_earned = Column(Numeric(12, 2), default=0)
    last_active_at = Column(DateTime)
    onboarded_at = Column(DateTime)
    first_deal_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deals = relationship("Deal", back_populates="partner")
    commissions = relationship("Commission", back_populates="partner")
    activities = relationship("ActivityLog", back_populates="partner")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)
    platform_job_id = Column(String(255))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    target_country = Column(String(3))
    target_language = Column(String(10))
    status = Column(String(20), default="draft")
    budget_type = Column(String(10))
    budget_amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    applications_count = Column(Integer, default=0)
    posted_at = Column(DateTime)
    expires_at = Column(DateTime)
    refreshed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    applications = relationship("Application", back_populates="job_posting")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    partner_id = Column(Integer, ForeignKey("partners.id"))
    platform = Column(String(20), nullable=False)
    platform_applicant_id = Column(String(255))
    applicant_name = Column(String(255), nullable=False)
    applicant_email = Column(String(255))
    applicant_country = Column(String(3))
    applicant_message = Column(Text)
    applicant_profile_url = Column(String(500))
    applicant_rating = Column(Numeric(3, 1))
    applicant_hourly_rate = Column(Numeric(8, 2))
    status = Column(String(20), default="new")
    auto_response_sent = Column(Boolean, default=False)
    screened_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    job_posting = relationship("JobPosting", back_populates="applications")
    partner = relationship("Partner")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255))
    client_company = Column(String(255))
    client_country = Column(String(3))
    client_industry = Column(String(100))
    deal_type = Column(String(10), default="annual")
    deal_value = Column(Numeric(12, 2), nullable=False)
    commission_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="prospect")
    closed_at = Column(DateTime)
    first_payment_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    partner = relationship("Partner", back_populates="deals")
    commissions = relationship("Commission", back_populates="deal")


class Commission(Base):
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="pending")
    held_reason = Column(String(255))
    period_start = Column(Date)
    period_end = Column(Date)
    paid_at = Column(DateTime)
    payment_method = Column(String(20))
    payment_reference = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    partner = relationship("Partner", back_populates="commissions")
    deal = relationship("Deal", back_populates="commissions")


class OutreachTemplate(Base):
    __tablename__ = "outreach_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    platform = Column(String(20), default="all")
    language = Column(String(10), default="en")
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    variables = Column(JSON, default=[])
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    action = Column(String(50), nullable=False)
    details = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())

    partner = relationship("Partner", back_populates="activities")
