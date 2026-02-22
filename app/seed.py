"""Seed data for Recruiter Pro — outreach templates + demo data."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    OutreachTemplate, Partner, JobPosting, Application, Deal, Commission, ActivityLog,
)

log = logging.getLogger(__name__)

TEMPLATES = [
    {
        "name": "Job Post — Upwork (English)",
        "type": "job_post",
        "platform": "upwork",
        "language": "en",
        "subject": None,
        "variables": [],
        "body": """Make $4,800 per deal. From your phone. No boss. No interview.

Gigabox is a complete business software platform \u2014 CRM, Help Desk, Analytics, Social Media, Finance, Legal, HR, Productivity, Research, Search, and more. One platform replaces expensive SaaS subscriptions for $2,000/month.

What you do:
- Know businesses that use software? Show them gigabox.app
- They switch, you earn 20% commission \u2014 $4,800 per annual deal
- We handle all setup, deployment, and support

What you get:
- Live demo platform you show from your phone
- Training materials in your language
- No quotas, no caps, earn at your own pace
- Paid in USD

All you need:
- A smartphone
- People in your network who run businesses
- Motivation to earn

Based in Southeast Asia? Even better \u2014 but we welcome partners worldwide.
This is NOT a job. This is income. High performers earn $2,000-8,000/month.

Tell us: What industries do you know? How many business owners are in your network?""",
    },
    {
        "name": "Job Post — Freelancer.com (Philippines)",
        "type": "job_post",
        "platform": "freelancer",
        "language": "tl",
        "subject": None,
        "variables": [],
        "body": """Earn \u20b1270,000+ per deal. No coding. No office. Just your phone and your network.

Gigabox is a complete business software platform. Companies pay $2,000/month for it. When you introduce a new client, you earn 20% = \u20b1270,000+ per annual deal.

What you need:
\u2705 Smartphone
\u2705 Know people who run businesses
\u2705 Can show a website on your phone
\u274c No experience required
\u274c No money upfront
\u274c No interview

This is real. Visit gigabox.app right now. The product is live.

One deal = \u20b1270,000. Two deals = \u20b1540,000. That\u2019s more than most annual salaries.

How to apply: Tell us your city, your background, and what industries you know.""",
    },
    {
        "name": "Job Post — Bahasa Melayu",
        "type": "job_post",
        "platform": "all",
        "language": "ms",
        "subject": None,
        "variables": [],
        "body": """Jana RM22,000 setiap perjanjian. Dari telefon anda. Tiada temuduga.

Gigabox ialah platform perisian perniagaan lengkap. Syarikat membayar $2,000/bulan untuknya. Apabila anda memperkenalkan pelanggan baharu, anda mendapat 20% = RM22,000+ setiap kontrak tahunan.

Yang anda perlukan:
\u2705 Telefon pintar
\u2705 Kenali orang yang menjalankan perniagaan
\u2705 Boleh tunjukkan laman web di telefon
\u274c Tiada pengalaman diperlukan
\u274c Tiada modal
\u274c Tiada temuduga

Ini nyata. Lawati gigabox.app sekarang. Produk ini sudah hidup.

Hubungi kami: Beritahu bandar anda, latar belakang, dan industri yang anda kenali.""",
    },
    {
        "name": "Auto-Response (English)",
        "type": "auto_response",
        "platform": "all",
        "language": "en",
        "subject": "Your Gigabox partner application \u2014 next steps",
        "variables": ["applicant_name"],
        "body": """Hi {applicant_name},

Thanks for your interest. Here\u2019s what to do next:

1. Visit gigabox.app/partners \u2014 full details on the program
2. Look at the live platform at gigabox.app \u2014 this is what you\u2019ll be showing
3. Reply with your WhatsApp number so we can connect directly

We review applications within 48 hours. No interview \u2014 if your profile fits, we onboard you immediately.

Quick reminder: one deal = $4,800 USD. No caps. No quotas.

Talk soon,
Gigabox Partner Team
info@gigabox.ai""",
    },
    {
        "name": "Follow-Up Day 3 (English)",
        "type": "follow_up",
        "platform": "all",
        "language": "en",
        "subject": "Quick follow-up \u2014 Gigabox partner opportunity",
        "variables": ["partner_name"],
        "body": """Hi {partner_name},

Following up on your partner application. Did you check out gigabox.app?

Quick recap:
- Show businesses a better software platform
- They pay $2,000/month
- You earn $4,800 per annual deal
- We handle everything technical

If you have questions, reply here or WhatsApp us.

Best,
Gigabox Partner Team
info@gigabox.ai""",
    },
    {
        "name": "Onboarding (English)",
        "type": "onboarding",
        "platform": "all",
        "language": "en",
        "subject": "Welcome to Gigabox Partners \u2014 let\u2019s get you earning",
        "variables": ["partner_name", "commission_rate", "territory"],
        "body": """Welcome {partner_name}!

You\u2019re now a Gigabox partner. Here\u2019s how to start:

1. LEARN THE PRODUCT (30 min)
   Visit gigabox.app. Click through every app. Understand what each one replaces.

2. IDENTIFY PROSPECTS
   Think of 5 businesses you know that use multiple software tools (CRM, help desk, project management, etc). These are your first targets.

3. SHOW THE PLATFORM
   Open gigabox.app on your phone. Walk them through the apps. Compare to what they\u2019re paying now.

4. CLOSE THE DEAL
   Interested? Connect them with us at info@gigabox.ai. We handle the demo, setup, and onboarding. You get $4,800 when they sign an annual contract.

5. LOG YOUR ACTIVITY
   After every prospect conversation, send us a quick debrief. This helps us support you better and improve the platform.

Your commission rate: {commission_rate}%
Your territory: {territory}

Questions? WhatsApp us anytime.

Let\u2019s earn,
Gigabox Partner Team""",
    },
]


def _seed_templates(db: Session):
    if db.query(OutreachTemplate).count() > 0:
        return
    log.info("[Seed] Creating %d outreach templates", len(TEMPLATES))
    for t in TEMPLATES:
        db.add(OutreachTemplate(**t))
    db.commit()


def _seed_demo_data(db: Session):
    """Seed demo partners, jobs, applications, deals, and commissions for the dashboard."""
    if db.query(Partner).count() > 0:
        return
    log.info("[Seed] Creating demo data for dashboard")

    now = datetime.utcnow()

    # Partners — 12 across countries and statuses
    partners_data = [
        ("Maria Santos", "maria.santos@email.com", "PH", "Manila", "sales", "active", "upwork", 3, 14400, ["PH", "ID"]),
        ("Ahmad bin Ismail", "ahmad.ismail@email.com", "MY", "Kuala Lumpur", "consulting", "active", "freelancer", 2, 9600, ["MY", "SG"]),
        ("Nguyen Thi Lan", "nguyen.lan@email.com", "VN", "Ho Chi Minh City", "tech", "active", "upwork", 1, 4800, ["VN"]),
        ("Somchai Phatthana", "somchai.p@email.com", "TH", "Bangkok", "marketing", "onboarded", "freelancer", 0, 0, ["TH"]),
        ("Rizal Pratama", "rizal.p@email.com", "ID", "Jakarta", "sales", "onboarded", "onlinejobs", 0, 0, ["ID"]),
        ("Fatima Abdullah", "fatima.a@email.com", "MY", "Penang", "accounting", "screening", "website", 0, 0, ["MY"]),
        ("Jose Reyes", "jose.r@email.com", "PH", "Cebu", "sales", "screening", "upwork", 0, 0, ["PH"]),
        ("Anh Tran", "anh.tran@email.com", "VN", "Hanoi", "consulting", "screening", "linkedin", 0, 0, ["VN"]),
        ("Budi Santoso", "budi.s@email.com", "ID", "Surabaya", "tech", "applied", "freelancer", 0, 0, []),
        ("Priya Kumari", "priya.k@email.com", "IN", "Mumbai", "marketing", "applied", "upwork", 0, 0, []),
        ("Carlos Garcia", "carlos.g@email.com", "ES", "Madrid", "sales", "applied", "linkedin", 0, 0, []),
        ("Rosa Flores", "rosa.f@email.com", "PH", "Davao", "other", "applied", "website", 0, 0, []),
    ]
    partners = []
    for i, (name, email, country, city, bg, status, source, deals, commission, territory) in enumerate(partners_data):
        p = Partner(
            name=name, email=email, country=country, city=city,
            background=bg, status=status, source=source,
            territory=territory, commission_rate=0.20,
            total_deals=deals,
            total_commission_earned=commission,
            onboarded_at=now - timedelta(days=30 - i * 2) if status in ("onboarded", "active") else None,
            first_deal_at=now - timedelta(days=20 - i) if deals > 0 else None,
            last_active_at=now - timedelta(days=i) if status == "active" else None,
            created_at=now - timedelta(days=45 - i * 3),
        )
        db.add(p)
        partners.append(p)
    db.flush()

    # Job Postings — 6 across platforms
    jobs_data = [
        ("upwork", "Commission Sales Partner — Southeast Asia", "active", "PH", "en"),
        ("upwork", "Business Development Partner — Global", "active", None, "en"),
        ("freelancer", "Partner Penjualan Komisi — Malaysia", "active", "MY", "ms"),
        ("freelancer", "Sales Partner — Philippines", "active", "PH", "tl"),
        ("website", "Gigabox Partner Program — Apply Now", "active", None, "en"),
        ("linkedin", "Strategic Partner — Enterprise Software", "draft", None, "en"),
    ]
    jobs = []
    for platform, title, status, country, lang in jobs_data:
        j = JobPosting(
            platform=platform, title=title, status=status,
            description=f"Earn $4,800+ per deal as a Gigabox partner. Target: {country or 'Global'}.",
            target_country=country, target_language=lang,
            budget_type="fixed", budget_amount=100,
            applications_count=0,
            posted_at=now - timedelta(days=14) if status == "active" else None,
            created_at=now - timedelta(days=15),
        )
        db.add(j)
        jobs.append(j)
    db.flush()

    # Applications — 18 across statuses
    app_statuses = ["new"] * 6 + ["reviewed"] * 3 + ["contacted"] * 2 + ["screened"] * 3 + ["accepted"] * 3 + ["rejected"] * 1
    app_names = [
        "Ana Lim", "Wei Chen", "Arjun Patel", "Siti Nurhaliza", "Tanaka Yuki", "Kim Soo-jin",
        "Marco Reyes", "Devi Sharma", "Liam O'Brien", "Mei Ling", "Rafael Costa",
        "Yusuf Ibrahim", "Hana Kim", "Paulo Santos", "Grace Tan",
        "Miguel Torres", "Nina Petrova", "Olga Kuznetsova",
    ]
    app_countries = ["PH", "CN", "IN", "MY", "JP", "KR", "PH", "IN", "US", "MY", "BR", "ID", "KR", "PH", "MY", "PH", "ID", "TH"]
    app_platforms = ["upwork", "freelancer", "upwork", "freelancer", "linkedin", "website"] * 3
    for i, (name, country, platform, status) in enumerate(zip(app_names, app_countries, app_platforms, app_statuses)):
        a = Application(
            job_posting_id=jobs[i % len(jobs)].id,
            platform=platform,
            applicant_name=name,
            applicant_email=f"{name.lower().replace(' ', '.').replace(chr(39), '')}@email.com",
            applicant_country=country,
            applicant_message=f"I'm interested in the partner program. I have a strong network in {country}.",
            applicant_rating=round(3.5 + (i % 15) * 0.1, 1),
            applicant_hourly_rate=round(10 + i * 2.5, 2),
            status=status,
            auto_response_sent=status not in ("new",),
            screened_at=now - timedelta(days=5) if status in ("screened", "accepted") else None,
            partner_id=partners[i].id if status == "accepted" and i < len(partners) else None,
            created_at=now - timedelta(days=20 - i),
        )
        db.add(a)

    # Update job application counts
    for j in jobs:
        j.applications_count = 3

    # Deals — 8 across pipeline stages
    deals_data = [
        (0, "TechCorp Manila", "techcorp@email.com", "TechCorp Inc", "PH", "Technology", "closed", 24000),
        (0, "RetailHub PH", "retail@email.com", "RetailHub", "PH", "Retail", "closed", 24000),
        (0, "BuildCon PH", "build@email.com", "BuildCon", "PH", "Construction", "closed", 24000),
        (1, "KL Solutions", "kl@email.com", "KL Solutions Sdn Bhd", "MY", "Consulting", "closed", 24000),
        (1, "Penang Trading", "penang@email.com", "Penang Trading Co", "MY", "Trading", "negotiation", 24000),
        (2, "Saigon Digital", "saigon@email.com", "Saigon Digital JSC", "VN", "Technology", "closed", 24000),
        (0, "Manila Foods", "manila@email.com", "Manila Foods Corp", "PH", "F&B", "demo", 24000),
        (1, "JB Enterprises", "jb@email.com", "JB Enterprises", "MY", "Manufacturing", "prospect", 24000),
    ]
    for partner_idx, client, email, company, country, industry, status, value in deals_data:
        partner = partners[partner_idx]
        commission_amt = value * 0.20
        d = Deal(
            partner_id=partner.id,
            client_name=client, client_email=email, client_company=company,
            client_country=country, client_industry=industry,
            deal_type="annual", deal_value=value, commission_amount=commission_amt,
            status=status,
            closed_at=now - timedelta(days=10) if status == "closed" else None,
            created_at=now - timedelta(days=25),
        )
        db.add(d)
        db.flush()

        # Create commissions for closed deals
        if status == "closed":
            c = Commission(
                partner_id=partner.id, deal_id=d.id,
                amount=commission_amt, currency="USD",
                status="paid" if partner_idx < 2 else "pending",
                paid_at=now - timedelta(days=5) if partner_idx < 2 else None,
                payment_method="wise" if partner_idx < 2 else None,
                created_at=now - timedelta(days=9),
            )
            db.add(c)

    # Activity log entries
    activities = [
        (partners[0].id, "deal_closed", {"client": "TechCorp Manila", "value": 24000}),
        (partners[0].id, "commission_paid", {"amount": 4800, "method": "wise"}),
        (partners[1].id, "deal_closed", {"client": "KL Solutions", "value": 24000}),
        (partners[0].id, "deal_closed", {"client": "RetailHub PH", "value": 24000}),
        (partners[2].id, "deal_closed", {"client": "Saigon Digital", "value": 24000}),
        (partners[3].id, "onboarded", {"country": "TH"}),
        (partners[4].id, "onboarded", {"country": "ID"}),
        (None, "posted_job", {"platform": "upwork", "title": "Commission Sales Partner"}),
        (None, "posted_job", {"platform": "freelancer", "title": "Partner Penjualan Komisi"}),
        (None, "received_application", {"name": "Ana Lim", "platform": "upwork"}),
        (None, "received_application", {"name": "Wei Chen", "platform": "freelancer"}),
        (None, "received_application", {"name": "Arjun Patel", "platform": "upwork"}),
        (partners[0].id, "deal_created", {"client": "Manila Foods", "value": 24000}),
        (partners[5].id, "screened", {"application_id": 6}),
        (partners[6].id, "screened", {"application_id": 7}),
        (None, "received_application", {"name": "Siti Nurhaliza", "platform": "freelancer"}),
        (None, "received_application", {"name": "Tanaka Yuki", "platform": "linkedin"}),
        (None, "received_application", {"name": "Kim Soo-jin", "platform": "website"}),
        (partners[1].id, "deal_created", {"client": "JB Enterprises", "value": 24000}),
        (None, "job_refreshed", {"platform": "upwork"}),
    ]
    for i, (pid, action, details) in enumerate(activities):
        db.add(ActivityLog(
            partner_id=pid, action=action, details=details,
            created_at=now - timedelta(hours=len(activities) - i),
        ))

    db.commit()
    log.info("[Seed] Demo data created: 12 partners, 6 jobs, 18 applications, 8 deals, 5 commissions, 20 activities")


def run_seed(db: Session):
    _seed_templates(db)
    _seed_demo_data(db)
