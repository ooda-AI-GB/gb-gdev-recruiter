import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION
from app.database import Base, engine, SessionLocal, get_db, serialize
from app.seed import run_seed

from app.routes import partners, jobs, applications, deals, commissions
from app.routes import templates, activities, dashboard, analytics
from app.routes.dashboard import dashboard as _dashboard_data
from app.routes.activities import recent_activities as _recent_activities

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("[Startup] Creating tables and seeding data")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    log.info("[Startup] %s %s ready", APP_NAME, APP_VERSION)
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Include all route modules
app.include_router(partners.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(deals.router)
app.include_router(commissions.router)
app.include_router(templates.router)
app.include_router(activities.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Recruiter Pro</title>
<style>
  :root {
    --bg: #0a0a0a; --surface: #141414; --border: #222; --text: #e5e5e5;
    --muted: #888; --accent: #f97316; --accent2: #22c55e; --accent3: #3b82f6;
    --red: #ef4444; --yellow: #eab308;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); }
  a { color: var(--accent); text-decoration: none; }

  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 240px; background: var(--surface); border-right: 1px solid var(--border);
    padding: 24px 16px; flex-shrink: 0;
  }
  .sidebar h1 { font-size: 18px; font-weight: 700; margin-bottom: 4px; color: var(--accent); }
  .sidebar .sub { font-size: 12px; color: var(--muted); margin-bottom: 32px; }
  .sidebar nav a {
    display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px;
    color: var(--muted); font-size: 14px; margin-bottom: 2px; transition: all .15s;
  }
  .sidebar nav a:hover, .sidebar nav a.active { background: rgba(249,115,22,.1); color: var(--accent); }
  .sidebar nav .divider { height: 1px; background: var(--border); margin: 12px 0; }

  .main { flex: 1; padding: 32px; overflow-y: auto; max-width: 1200px; }
  .main h2 { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
  .main .subtitle { color: var(--muted); font-size: 14px; margin-bottom: 24px; }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
  .stat-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;
  }
  .stat-card .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
  .stat-card .value { font-size: 32px; font-weight: 700; margin: 4px 0; }
  .stat-card .change { font-size: 12px; color: var(--accent2); }
  .stat-card .value.orange { color: var(--accent); }
  .stat-card .value.green { color: var(--accent2); }
  .stat-card .value.blue { color: var(--accent3); }

  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }
  .grid3 { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 32px; }

  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;
  }
  .card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  .card h3 .badge {
    font-size: 11px; background: rgba(249,115,22,.15); color: var(--accent);
    padding: 2px 8px; border-radius: 12px; font-weight: 500;
  }

  /* Funnel */
  .funnel { display: flex; flex-direction: column; gap: 6px; }
  .funnel-row { display: flex; align-items: center; gap: 12px; }
  .funnel-label { width: 100px; font-size: 13px; color: var(--muted); text-align: right; }
  .funnel-bar { height: 28px; border-radius: 6px; display: flex; align-items: center; padding: 0 12px;
    font-size: 13px; font-weight: 600; color: #fff; min-width: 40px; transition: width .6s ease; }
  .funnel-bar.s1 { background: var(--accent3); }
  .funnel-bar.s2 { background: #6366f1; }
  .funnel-bar.s3 { background: #8b5cf6; }
  .funnel-bar.s4 { background: var(--accent); }
  .funnel-bar.s5 { background: var(--yellow); }
  .funnel-bar.s6 { background: var(--accent2); }

  /* Country bars */
  .country-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .country-code { width: 30px; font-size: 13px; font-weight: 600; }
  .country-bar { height: 22px; background: var(--accent); border-radius: 4px; min-width: 8px; transition: width .5s; }
  .country-count { font-size: 13px; color: var(--muted); }

  /* Table */
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 11px; color: var(--muted); text-transform: uppercase;
    letter-spacing: .5px; padding: 8px 12px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 12px; font-size: 13px; border-bottom: 1px solid var(--border); }
  tr:hover td { background: rgba(255,255,255,.02); }
  .status-badge {
    display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
  }
  .status-badge.active, .status-badge.closed, .status-badge.paid { background: rgba(34,197,94,.15); color: var(--accent2); }
  .status-badge.onboarded, .status-badge.approved { background: rgba(59,130,246,.15); color: var(--accent3); }
  .status-badge.screening, .status-badge.pending, .status-badge.prospect { background: rgba(234,179,8,.15); color: var(--yellow); }
  .status-badge.applied, .status-badge.new, .status-badge.demo { background: rgba(249,115,22,.15); color: var(--accent); }
  .status-badge.negotiation { background: rgba(139,92,246,.15); color: #a78bfa; }
  .status-badge.lost, .status-badge.rejected, .status-badge.inactive { background: rgba(239,68,68,.15); color: var(--red); }

  /* Activity feed */
  .activity-item { display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border); }
  .activity-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
  .activity-dot.deal { background: var(--accent2); }
  .activity-dot.partner { background: var(--accent3); }
  .activity-dot.app { background: var(--accent); }
  .activity-dot.job { background: var(--yellow); }
  .activity-dot.commission { background: #a78bfa; }
  .activity-text { font-size: 13px; }
  .activity-time { font-size: 11px; color: var(--muted); }

  /* Pipeline columns */
  .pipeline { display: flex; gap: 12px; }
  .pipeline-col { flex: 1; }
  .pipeline-header { font-size: 12px; color: var(--muted); text-transform: uppercase; margin-bottom: 8px;
    display: flex; justify-content: space-between; }
  .pipeline-card {
    background: rgba(255,255,255,.03); border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 12px; margin-bottom: 6px; font-size: 13px;
  }
  .pipeline-card .client { font-weight: 600; }
  .pipeline-card .partner { color: var(--muted); font-size: 12px; }
  .pipeline-card .amount { color: var(--accent2); font-weight: 600; font-size: 12px; }

  .loading { text-align: center; padding: 40px; color: var(--muted); }

  @media (max-width: 900px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--border); padding: 16px; }
    .sidebar nav { display: flex; flex-wrap: wrap; gap: 4px; }
    .sidebar nav .divider { display: none; }
    .stats { grid-template-columns: repeat(2, 1fr); }
    .grid2, .grid3 { grid-template-columns: 1fr; }
    .pipeline { flex-direction: column; }
  }
</style>
</head>
<body>
<div class="layout">
  <div class="sidebar">
    <h1>Recruiter Pro</h1>
    <div class="sub">Partner Network Intelligence</div>
    <nav>
      <a href="/" class="active">Dashboard</a>
      <a href="/docs">API Docs</a>
      <div class="divider"></div>
      <a href="/docs#/Partners">Partners</a>
      <a href="/docs#/Job%20Postings">Job Postings</a>
      <a href="/docs#/Applications">Applications</a>
      <a href="/docs#/Deals">Deals</a>
      <a href="/docs#/Commissions">Commissions</a>
      <a href="/docs#/Outreach%20Templates">Templates</a>
      <a href="/docs#/Analytics">Analytics</a>
    </nav>
  </div>

  <div class="main">
    <h2>Recruitment Dashboard</h2>
    <div class="subtitle">Partner network performance and pipeline overview</div>

    <div class="stats" id="stats">
      <div class="stat-card"><div class="label">Total Partners</div><div class="value" id="s-partners">-</div><div class="change" id="s-partners-new"></div></div>
      <div class="stat-card"><div class="label">Active Partners</div><div class="value green" id="s-active">-</div></div>
      <div class="stat-card"><div class="label">Open Applications</div><div class="value orange" id="s-apps">-</div><div class="change" id="s-apps-week"></div></div>
      <div class="stat-card"><div class="label">Pipeline Value</div><div class="value blue" id="s-pipeline">-</div><div class="change" id="s-deals-month"></div></div>
    </div>

    <div class="grid2">
      <div class="card">
        <h3>Recruitment Funnel</h3>
        <div class="funnel" id="funnel"></div>
      </div>
      <div class="card">
        <h3>Partners by Country</h3>
        <div id="countries"></div>
      </div>
    </div>

    <div class="grid3">
      <div class="card">
        <h3>Partner Leaderboard <span class="badge">Top Performers</span></h3>
        <table>
          <thead><tr><th>#</th><th>Partner</th><th>Country</th><th>Deals</th><th>Commission</th></tr></thead>
          <tbody id="leaderboard"></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Recent Activity</h3>
        <div id="activity"></div>
      </div>
    </div>

    <div class="card" style="margin-bottom:32px">
      <h3>Deal Pipeline</h3>
      <div class="pipeline" id="pipeline"></div>
    </div>
  </div>
</div>

<script>
// Data injected server-side — no auth needed for dashboard view
const DASH_DATA = __DASH_DATA__;
const ACTIVITIES_DATA = __ACTIVITIES_DATA__;
const DEALS_DATA = __DEALS_DATA__;

function $(id) { return document.getElementById(id); }
function fmt(n) { return n >= 1000 ? '$' + (n/1000).toFixed(0) + 'K' : '$' + n.toLocaleString(); }

async function loadDashboard() {
  try {
    const dash = DASH_DATA;
    const activities = ACTIVITIES_DATA;
    const deals = DEALS_DATA;

    // Stats
    $('s-partners').textContent = dash.partners.total;
    $('s-partners-new').textContent = '+' + dash.partners.new_this_week + ' this week';
    $('s-active').textContent = (dash.partners.by_status.active || 0);
    $('s-apps').textContent = dash.applications.total;
    $('s-apps-week').textContent = '+' + dash.applications.this_week + ' this week';
    const pipelineValue = Object.values(dash.deals.pipeline || {}).reduce((a, b) => a + b, 0) * 24000;
    $('s-pipeline').textContent = fmt(dash.deals.total_value_closed || pipelineValue);
    $('s-deals-month').textContent = dash.deals.this_month + ' deals this month';

    // Funnel
    const f = dash.funnel;
    const maxF = Math.max(f.applications, 1);
    const stages = [
      ['Postings', f.postings, 's1'],
      ['Applications', f.applications, 's2'],
      ['Screened', f.screened, 's3'],
      ['Onboarded', f.onboarded, 's4'],
      ['First Deal', f.first_deal, 's5'],
    ];
    $('funnel').innerHTML = stages.map(([label, count, cls]) => {
      const w = Math.max(count / maxF * 100, 8);
      return '<div class="funnel-row"><div class="funnel-label">' + label +
        '</div><div class="funnel-bar ' + cls + '" style="width:' + w + '%">' + count + '</div></div>';
    }).join('') + '<div style="margin-top:8px;font-size:13px;color:var(--muted)">Conversion: <strong style="color:var(--accent2)">' + f.conversion_rate + '</strong></div>';

    // Countries
    const countries = Object.entries(dash.partners.by_country).sort((a, b) => b[1] - a[1]);
    const maxC = countries.length ? countries[0][1] : 1;
    $('countries').innerHTML = countries.map(([code, count]) => {
      const w = Math.max(count / maxC * 100, 8);
      return '<div class="country-row"><div class="country-code">' + code +
        '</div><div class="country-bar" style="width:' + w + '%"></div><div class="country-count">' + count + '</div></div>';
    }).join('');

    // Leaderboard
    $('leaderboard').innerHTML = dash.leaderboard.length ?
      dash.leaderboard.map((p, i) =>
        '<tr><td>' + (i + 1) + '</td><td><strong>' + p.name + '</strong></td><td>' +
        p.country + '</td><td>' + p.deals + '</td><td style="color:var(--accent2);font-weight:600">' +
        fmt(p.commission) + '</td></tr>'
      ).join('') :
      '<tr><td colspan="5" style="text-align:center;color:var(--muted)">No deals yet</td></tr>';

    // Activity
    const actionColors = {
      deal_closed: 'deal', deal_created: 'deal', deal_lost: 'deal',
      partner_created: 'partner', onboarded: 'partner', screened: 'partner',
      received_application: 'app', sent_response: 'app', rejected_application: 'app',
      posted_job: 'job', job_refreshed: 'job', job_closed: 'job',
      commission_paid: 'commission', commission_approved: 'commission', commission_held: 'commission',
    };
    const actionLabels = {
      deal_closed: 'Deal closed', deal_created: 'New deal', deal_lost: 'Deal lost',
      partner_created: 'New partner', onboarded: 'Partner onboarded', screened: 'Application screened',
      received_application: 'New application', sent_response: 'Response sent',
      posted_job: 'Job posted', job_refreshed: 'Job refreshed', job_closed: 'Job closed',
      commission_paid: 'Commission paid', commission_approved: 'Commission approved',
      rejected_application: 'Application rejected', commission_held: 'Commission held',
    };
    $('activity').innerHTML = (activities || []).slice(0, 15).map(a => {
      const color = actionColors[a.action] || 'app';
      const label = actionLabels[a.action] || a.action;
      const detail = a.details ? (a.details.client || a.details.name || a.details.platform || a.details.amount || '') : '';
      const time = a.created_at ? new Date(a.created_at).toLocaleString() : '';
      return '<div class="activity-item"><div class="activity-dot ' + color +
        '"></div><div><div class="activity-text">' + label + (detail ? ' — ' + detail : '') +
        '</div><div class="activity-time">' + time + '</div></div></div>';
    }).join('');

    // Pipeline
    const pipeStages = ['prospect', 'demo', 'negotiation', 'closed', 'lost'];
    const pipeLabels = { prospect: 'Prospect', demo: 'Demo', negotiation: 'Negotiation', closed: 'Closed', lost: 'Lost' };
    const dealItems = (deals && deals.items) ? deals.items : [];
    $('pipeline').innerHTML = pipeStages.map(stage => {
      const stageDeals = dealItems.filter(d => d.status === stage);
      return '<div class="pipeline-col"><div class="pipeline-header"><span>' + pipeLabels[stage] +
        '</span><span>' + stageDeals.length + '</span></div>' +
        stageDeals.map(d =>
          '<div class="pipeline-card"><div class="client">' + d.client_name +
          '</div><div class="partner">' + (d.client_company || '') +
          '</div><div class="amount">' + fmt(d.deal_value) + '</div></div>'
        ).join('') + '</div>';
    }).join('');

  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}

loadDashboard();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def root_dashboard(request: Request, db: Session = Depends(get_db)):
    from app.models import Deal
    # Fetch data server-side to embed in HTML (no auth required for the dashboard view)
    dash_data = _dashboard_data(db=db, _="server")
    act_data = _recent_activities(db=db, _="server")
    deals_query = db.query(Deal).order_by(Deal.created_at.desc()).limit(20).all()
    deals_data = {"total": len(deals_query), "items": [serialize(d) for d in deals_query]}

    html = DASHBOARD_HTML
    html = html.replace("__DASH_DATA__", json.dumps(dash_data, default=str))
    html = html.replace("__ACTIVITIES_DATA__", json.dumps(act_data, default=str))
    html = html.replace("__DEALS_DATA__", json.dumps(deals_data, default=str))
    return HTMLResponse(content=html)
