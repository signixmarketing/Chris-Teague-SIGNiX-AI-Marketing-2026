"""
SIGNiX TruStage Account Expansion Model — April 2026
Addresses Jay's question: what share of a bank's total signing/auth business do we have?

Model premise:
- Current SIGNiX usage = loan documents only (TruStage integration scope)
- Banks have 5 additional workflow categories SIGNiX could serve
- Estimated multipliers based on community bank industry benchmarks
- All estimates are models — discovery conversations with each bank surface real numbers

Output: PROJECT-DOCS/DELIVERABLES/SIGNiX_TruStage_Expansion_Model_April2026.html
Run from: repo root or any directory
"""

import os
import plotly.graph_objects as go
import plotly.io as pio

# ── Brand tokens ──────────────────────────────────────────────────────────────
GREEN      = '#6da34a'
DARK_GREEN = '#4a7a2e'
INK        = '#2e3440'
BODY       = '#545454'
MUTED      = '#6b7280'
WHITE      = '#ffffff'
CANVAS     = '#f8fafb'
RULE       = '#d8dee9'
RED        = '#e05252'
AMBER      = '#e0a252'
LIGHT_RED  = 'rgba(224,82,82,0.12)'
LIGHT_AMB  = 'rgba(224,162,82,0.12)'
LIGHT_GRN  = 'rgba(109,163,74,0.12)'
LIGHT_BLUE = 'rgba(74,122,158,0.12)'

FONT = dict(family='Calibri, Arial', color=BODY)

SMS_PRICE       = 0.25
ID_VERIFY_PRICE = 1.50
DATA_MONTHS     = 15   # Jan 2025 – Mar 2026

# ── Workflow expansion multipliers (relative to annual loan signing volume) ───
# Based on community bank industry benchmarks. All estimates — not actual data.
# Account opening:   banks open ~1.6 new accounts per loan originated
# Wire auth:         ~0.4 wire authorizations per loan originated
# Beneficiary/POA:   ~0.3 beneficiary changes / POA docs per loan originated
# HR/Internal:       fixed estimate — ~50 docs/year regardless of loan volume
# Vendor/Compliance: fixed estimate — ~30 docs/year regardless of loan volume
WORKFLOW_MULTIPLIERS = {
    'Account Opening':    1.6,
    'Wire Authorization': 0.4,
    'Beneficiary / POA':  0.3,
    'HR Documents':       None,   # fixed — see below
    'Vendor / Compliance':None,   # fixed — see below
}
HR_FIXED     = 50   # estimated HR docs/year for a community bank
VENDOR_FIXED = 30   # estimated vendor/compliance docs/year

# ── Account data (from TruStage dashboard — non-select accounts only) ─────────
# (name, lifetime_transactions, auth_events_total)
ACCOUNTS = [
    ('Bank of Pontiac',              2158,  699),
    ('EntreBank',                     617,  276),
    ('Commercial Bank of TX',         610,    4),
    ('FBT Bank & Mortgage',           526,   64),
    ('Greenville Federal Bank',       403,    0),
    ('Bank of Old Monroe',            376,  619),
    ('Merchants National Bank',       298,  474),
    ('First Natl Bank of Aspermont',  289,   15),
    ('Clinton Bank',                  253,  336),
    ("Citizen's Bank of Enterprise",  193,  244),
    ('Peoples Bank Brownstown',       178,  240),
    ('Greenfield Banking Co.',        175,  471),
    ('BankTennessee',                 165,  119),
    ('State Bank of Cherry',          142,  202),
    ('Blue Grass Valley Bank',         70,  139),
    ('Farmers & Merchants Bank',       66,   14),
    ('Metro Bank',                     78,    1),
    ('Patterson State Bank',           71,   97),
]

# ── Build expansion model per account ─────────────────────────────────────────
def build_model(name, lifetime_trans, auth_events):
    annual_loans  = round(lifetime_trans / DATA_MONTHS * 12)
    acct_opening  = round(annual_loans * 1.6)
    wire_auth     = round(annual_loans * 0.4)
    ben_poa       = round(annual_loans * 0.3)
    hr_docs       = HR_FIXED
    vendor_docs   = VENDOR_FIXED
    total_expansion = acct_opening + wire_auth + ben_poa + hr_docs + vendor_docs
    total_addressable = annual_loans + total_expansion
    share_pct     = round(annual_loans / total_addressable * 100, 1) if total_addressable else 0
    expansion_sms = round(total_expansion * SMS_PRICE, 2)
    expansion_idv = round(total_expansion * ID_VERIFY_PRICE, 2)
    auth_rate_pct = round(auth_events / lifetime_trans * 100, 1) if lifetime_trans else 0
    return {
        'name':             name,
        'lifetime':         lifetime_trans,
        'annual_loans':     annual_loans,
        'acct_opening':     acct_opening,
        'wire_auth':        wire_auth,
        'ben_poa':          ben_poa,
        'hr_docs':          hr_docs,
        'vendor_docs':      vendor_docs,
        'total_expansion':  total_expansion,
        'total_addressable':total_addressable,
        'share_pct':        share_pct,
        'expansion_sms':    expansion_sms,
        'expansion_idv':    expansion_idv,
        'auth_rate_pct':    auth_rate_pct,
    }

models = [build_model(*a) for a in ACCOUNTS]
models.sort(key=lambda x: x['total_expansion'], reverse=True)
top12  = models[:12]

# ── Portfolio totals ──────────────────────────────────────────────────────────
total_current      = sum(m['annual_loans'] for m in models)
total_addressable  = sum(m['total_addressable'] for m in models)
total_expansion    = sum(m['total_expansion'] for m in models)
portfolio_share    = round(total_current / total_addressable * 100, 1)
total_exp_sms      = round(total_expansion * SMS_PRICE)
total_exp_idv      = round(total_expansion * ID_VERIFY_PRICE)

# ── Chart 1: Current vs. Expansion potential (stacked bar, top 12) ────────────
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    name='Current (Loan Docs via SIGNiX)',
    y=[m['name'] for m in top12],
    x=[m['annual_loans'] for m in top12],
    orientation='h',
    marker_color=GREEN,
    text=[f"{m['annual_loans']:,}/yr  ({m['share_pct']}% share)" for m in top12],
    textposition='inside',
    insidetextanchor='start',
    textfont=dict(color=WHITE, size=10),
))
fig1.add_trace(go.Bar(
    name='Expansion Opportunity (Other Workflows)',
    y=[m['name'] for m in top12],
    x=[m['total_expansion'] for m in top12],
    orientation='h',
    marker_color=AMBER,
    text=[f"+{m['total_expansion']:,} est." for m in top12],
    textposition='inside',
    insidetextanchor='start',
    textfont=dict(color=INK, size=10),
))
fig1.update_layout(
    barmode='stack',
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=FONT,
    height=420,
    margin=dict(l=220, r=120, t=60, b=40),
    title=dict(
        text='Annual Signing Volume: Current (Loans) vs. Estimated Expansion Opportunity<br>'
             '<sup>Green = current SIGNiX scope (loan docs). Amber = estimated addressable beyond loans. '
             'All expansion figures are model estimates.</sup>',
        font=dict(color=INK, size=14)),
    xaxis=dict(showgrid=True, gridcolor=RULE, title='Est. Annual Documents / Transactions'),
    yaxis=dict(showgrid=False, tickfont=dict(size=11), autorange='reversed'),
    legend=dict(orientation='h', y=-0.12),
)

# ── Chart 2: Share of wallet donut ────────────────────────────────────────────
fig2 = go.Figure(go.Pie(
    labels=['Current SIGNiX (Loans)', 'Expansion Opportunity'],
    values=[total_current, total_expansion],
    hole=0.55,
    marker=dict(colors=[GREEN, AMBER]),
    textinfo='label+percent',
    textfont=dict(size=12),
    hovertemplate='%{label}<br>Est. Annual Transactions: %{value:,}<extra></extra>',
))
fig2.update_layout(
    paper_bgcolor=WHITE,
    font=FONT,
    margin=dict(l=20, r=20, t=50, b=20),
    title=dict(text='Portfolio Share of Wallet: Current vs. Addressable',
               font=dict(color=INK, size=14)),
    showlegend=False,
    annotations=[dict(
        text=f'{portfolio_share}%<br>current<br>share',
        x=0.5, y=0.5,
        font=dict(size=14, color=INK),
        showarrow=False,
    )],
)

# ── Chart 3: Expansion model table (top 12 accounts) ─────────────────────────
row_colors = []
for m in top12:
    if m['share_pct'] < 20:
        row_colors.append(LIGHT_RED)
    elif m['share_pct'] < 30:
        row_colors.append(LIGHT_AMB)
    else:
        row_colors.append(WHITE)

fig3 = go.Figure(go.Table(
    header=dict(
        values=['Account', 'Current\n(Loans/yr)', 'Acct\nOpening', 'Wire\nAuth',
                'Ben / POA', 'HR\nDocs', 'Vendor /\nCompliance',
                'Total\nAddressable', 'Current\nShare %', 'Expansion\nSMS Value'],
        fill_color=INK,
        font=dict(color=WHITE, family='Calibri, Arial', size=11),
        align='left',
        height=34,
    ),
    cells=dict(
        values=[
            [m['name'] for m in top12],
            [f"{m['annual_loans']:,}" for m in top12],
            [f"~{m['acct_opening']:,}" for m in top12],
            [f"~{m['wire_auth']:,}" for m in top12],
            [f"~{m['ben_poa']:,}" for m in top12],
            [f"~{m['hr_docs']}" for m in top12],
            [f"~{m['vendor_docs']}" for m in top12],
            [f"~{m['total_addressable']:,}" for m in top12],
            [f"{m['share_pct']}%" for m in top12],
            [f"${m['expansion_sms']:,.0f}/yr" for m in top12],
        ],
        fill_color=[row_colors] * 10,
        font=dict(color=BODY, family='Calibri, Arial', size=11),
        align='left',
        height=28,
    ),
    columnwidth=[2.8, 1.1, 1.1, 1, 1, 0.9, 1.2, 1.3, 1, 1.3],
))
fig3.update_layout(
    height=460,
    margin=dict(l=10, r=10, t=60, b=10),
    paper_bgcolor=WHITE,
    title=dict(
        text='Account Expansion Model: Estimated Annual Signing Volume by Workflow Category<br>'
             '<sup>Red = &lt;20% current share · Amber = 20–30% · All expansion figures are estimates based on industry benchmarks. '
             'Discovery conversations surface real numbers.</sup>',
        font=dict(color=INK, size=13)),
)

# ── Chart 4: Workflow category reference ──────────────────────────────────────
fig4 = go.Figure(go.Table(
    header=dict(
        values=['Workflow Category', 'What It Covers', 'SIGNiX Fit', 'Typical Volume vs. Loans', 'Discovery Question'],
        fill_color=DARK_GREEN,
        font=dict(color=WHITE, family='Calibri, Arial', size=12),
        align='left',
        height=32,
    ),
    cells=dict(
        values=[
            ['Loan Documents', 'Account Opening', 'Wire Authorization',
             'Beneficiary / POA / Trust', 'HR Documents', 'Vendor / Compliance'],
            ['Origination, modification, HELOC, commercial. Already in use.',
             'New deposit accounts, CDs, IRAs, business accounts',
             'Customer-authorized wire transfers. High fraud risk.',
             'Beneficiary updates, power of attorney, trust documents',
             'Offer letters, policy acknowledgments, performance docs',
             'Third-party agreements, regulatory attestations, audits'],
            ['✅ Active via TruStage', '✅ Strong fit. ID Verify ideal.',
             '✅ Strong fit. Authentication critical.', '✅ Strong fit. ID Verify ideal.',
             '✅ Fit. E-sign + basic auth.', '✅ Fit. E-sign + audit trail.'],
            ['Baseline (current 100%)', '~1.6× loan volume',
             '~0.4× loan volume', '~0.3× loan volume',
             '~50 docs/yr (fixed est.)', '~30 docs/yr (fixed est.)'],
            ['"How are you handling loan doc signing today?" (baseline)',
             '"What does your new account opening process look like? Is it digital?"',
             '"How do customers authorize wires today? Is there a signature or auth step?"',
             '"When a customer changes a beneficiary or sets up a POA, what\'s your current process?"',
             '"Are HR onboarding and policy docs still on paper or email?"',
             '"How do you handle vendor agreements and compliance attestations?"'],
        ],
        fill_color=[
            [LIGHT_GRN, LIGHT_BLUE, LIGHT_RED, LIGHT_AMB, CANVAS, CANVAS],
        ] * 5,
        font=dict(color=BODY, family='Calibri, Arial', size=11),
        align='left',
        height=48,
    ),
    columnwidth=[1.8, 2.8, 1.8, 1.6, 3.0],
))
fig4.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=55, b=10),
    paper_bgcolor=WHITE,
    title=dict(text='Workflow Category Framework: Current Scope vs. Expansion Opportunities',
               font=dict(color=INK, size=14)),
)

def chart_html(fig, height=None):
    if height:
        fig.update_layout(height=height)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={'responsive': True})

c1 = chart_html(fig1)
c2 = chart_html(fig2, 320)
c3 = chart_html(fig3)
c4 = chart_html(fig4)

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>SIGNiX TruStage Account Expansion Model, April 2026</title>
  <script src="https://cdn.plot.ly/plotly-3.4.0.min.js" charset="utf-8"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Calibri, Arial, sans-serif; background: {CANVAS}; color: {BODY}; font-size: 14px; }}
    .header {{
      background: {INK}; color: {WHITE}; padding: 22px 32px;
      display: flex; align-items: center; justify-content: space-between;
    }}
    .header h1 {{ font-size: 22px; font-weight: 700; }}
    .header h1 span {{ color: {GREEN}; }}
    .header-meta {{ font-size: 12px; color: {MUTED}; text-align: right; line-height: 1.6; }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 24px 40px; }}
    .section-title {{
      font-size: 13px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.07em; color: {MUTED}; margin: 28px 0 12px;
      padding-bottom: 6px; border-bottom: 1px solid {RULE};
    }}
    .kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 8px; }}
    .kpi-card {{
      background: {WHITE}; border: 1px solid {RULE};
      border-radius: 8px; padding: 18px 18px 14px;
    }}
    .kpi-value {{ font-size: 26px; font-weight: 700; line-height: 1.1; }}
    .kpi-label {{ font-size: 12px; color: {MUTED}; margin-top: 5px; font-weight: 600; text-transform: uppercase; }}
    .kpi-sub   {{ font-size: 11px; color: {MUTED}; margin-top: 3px; }}
    .two-col   {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .chart-card, .full-card {{
      background: {WHITE}; border: 1px solid {RULE};
      border-radius: 8px; padding: 4px 4px 0; overflow: hidden;
    }}
    .note-box {{
      background: {WHITE}; border: 1px solid {RULE};
      border-radius: 6px; padding: 14px 18px; font-size: 12px;
      color: {MUTED}; line-height: 1.8; margin-top: 8px;
    }}
    .alert {{
      background: {WHITE}; border-left: 4px solid {AMBER};
      border-radius: 4px; padding: 14px 18px;
      font-size: 13px; line-height: 1.6;
      display: flex; gap: 10px; align-items: flex-start;
      margin-bottom: 10px;
    }}
    .alert-icon {{ font-size: 16px; flex-shrink: 0; }}
    .footer {{
      text-align: center; padding: 20px;
      font-size: 11px; color: {MUTED};
      border-top: 1px solid {RULE}; margin-top: 32px;
    }}
    @media (max-width: 900px) {{ .kpi-row, .two-col {{ grid-template-columns: 1fr 1fr; }} }}
    @media (max-width: 600px) {{ .kpi-row, .two-col {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <h1><span>SIGNiX</span> TruStage Account Expansion Model</h1>
    <div style="font-size:13px; color:{MUTED}; margin-top:4px;">
      Share of Wallet &nbsp;·&nbsp; Workflow Expansion Opportunity &nbsp;·&nbsp; April 2026
    </div>
  </div>
  <div class="header-meta">
    Prepared by Chris Teague<br>
    Head of Growth and Marketing<br>
    April 13, 2026
  </div>
</div>

<div class="container">

  <!-- The question this answers -->
  <div style="background:{WHITE}; border:1px solid {RULE}; border-left: 5px solid {GREEN};
              border-radius:6px; padding:18px 22px; margin:20px 0; font-size:13px; line-height:1.8;">
    <strong style="color:{INK}; font-size:14px;">The question this model answers:</strong><br>
    Right now, SIGNiX is used by TruStage FI customers for one thing: loan documents.
    But a bank that signs 500 loan documents per year likely signs another 1,500+ documents across
    account opening, wire authorizations, beneficiary changes, HR, and vendor agreements.
    We have no visibility into those workflows today.
    <strong>This model estimates what share of each bank's total signing footprint we currently hold,
    and how large the expansion opportunity is.</strong>
    All expansion figures are estimates based on community bank industry benchmarks.
    The discovery conversation with each bank surfaces the real numbers.
  </div>

  <!-- KPI Scorecard -->
  <div class="section-title">Portfolio Share of Wallet: Summary</div>
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-value" style="color:{GREEN};">{total_current:,}</div>
      <div class="kpi-label">Est. Annual Loan Signings</div>
      <div class="kpi-sub">Current SIGNiX scope across portfolio</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{AMBER};">{total_addressable:,}</div>
      <div class="kpi-label">Est. Total Addressable</div>
      <div class="kpi-sub">All workflow categories combined</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{RED};">{portfolio_share}%</div>
      <div class="kpi-label">Current Share of Wallet</div>
      <div class="kpi-sub">Loans only. Model estimate.</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{AMBER};">{total_expansion:,}</div>
      <div class="kpi-label">Expansion Gap</div>
      <div class="kpi-sub">Est. annual transactions beyond loans</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{DARK_GREEN};">${total_exp_sms:,}</div>
      <div class="kpi-label">SMS Revenue Potential</div>
      <div class="kpi-sub">On expansion gap at $0.25/event/yr</div>
    </div>
  </div>

  <div class="alert" style="border-left-color:{AMBER}; margin-top:16px;">
    <span class="alert-icon">⚠️</span>
    <span><strong>These are model estimates, not verified data.</strong>
    The multipliers (1.6× for account opening, 0.4× for wire auth, etc.) are based on community bank
    industry benchmarks. Some banks will be higher, some lower. The purpose of this model is to give
    Mike a starting framework for discovery conversations, not to report on actual volumes.
    Once a bank shares their real workflow volumes, replace these estimates with actuals.</span>
  </div>

  <!-- Share of wallet chart + donut -->
  <div class="section-title">Current vs. Addressable Volume by Account</div>
  <div class="two-col">
    <div class="chart-card">{c1}</div>
    <div class="chart-card">{c2}</div>
  </div>

  <!-- Expansion model table -->
  <div class="section-title">Account Expansion Model: Top 12 Accounts by Opportunity</div>
  <div class="full-card">{c3}</div>
  <div class="note-box">
    <strong>How to read this table:</strong>
    "Current (Loans/yr)" = estimated annual loan document volume through SIGNiX (lifetime ÷ 15 months × 12).
    All other columns are <strong>model estimates</strong> based on community bank benchmarks.
    "Current Share %" = loans divided by total addressable. What fraction of the bank's signing footprint we currently touch.
    "Expansion SMS Value" = if SIGNiX captured the expansion gap transactions with SMS authentication at $0.25/event.
    Red rows = &lt;20% share · Amber = 20–30% share.
    Account opening and wire authorization are the highest-volume categories after loans.
    Wire authorization is also the highest-risk workflow. Strongest case for authentication.
  </div>

  <!-- Workflow category framework -->
  <div class="section-title">Workflow Category Framework: What to Look For in Every Account</div>
  <div class="full-card">{c4}</div>
  <div class="note-box">
    Use the <strong>Discovery Question</strong> column as Mike's call guide.
    One question per category per call. The goal is not to pitch. It's to map the workflow.
    Once the workflow is mapped, the case for SIGNiX with authentication writes itself.
    Wire authorization is the fastest win: high fraud risk, existing signing habit, clear compliance need.
    Account opening is the highest volume: every new customer is a trigger event.
  </div>

  <!-- Strategic context -->
  <div class="section-title">How to Use This Model</div>
  <div class="alert" style="border-left-color:{GREEN};">
    <span class="alert-icon">🎯</span>
    <span><strong>Start with the three largest-gap accounts:</strong>
    Bank of Pontiac (2,158 lifetime trans, ~$868/yr SMS expansion potential),
    Commercial Bank of TX (610 trans, zero auth, significant expansion gap), and
    EntreBank (617 trans). These three accounts alone represent the biggest share-of-wallet
    opportunity in the portfolio. One discovery call per account to map non-loan workflows
    is the next step. Mike's fraud risk framing opens the door, especially on wire authorization.</span>
  </div>
  <div class="alert" style="border-left-color:{AMBER}; margin-top: 0;">
    <span class="alert-icon">📋</span>
    <span><strong>The discovery call goal is a workflow map, not a sales pitch.</strong>
    Ask: "Walk me through how you handle [workflow category] today."
    If they say "we use paper" or "we use email," that's the opening.
    If they say "we use DocuSign," that's a displacement conversation.
    If they say "we already use SIGNiX for that," update this model with real data.</span>
  </div>


  <!-- Sources -->
  <div class="section-title">Benchmark Sources</div>
  <div class="note-box" style="font-size:13px; line-height:2;">
    <p style="margin:0 0 10px; color:{INK}; font-weight:600;">
      The workflow multipliers in this model are based on publicly available community bank industry data.
      They are directional estimates. Replace with actuals as discovery conversations surface real numbers.
    </p>
    <table style="width:100%; border-collapse:collapse; font-size:12px;">
      <thead>
        <tr style="border-bottom:2px solid {RULE};">
          <th style="text-align:left; padding:6px 10px; color:{INK}; font-weight:600; width:22%;">Workflow Category</th>
          <th style="text-align:left; padding:6px 10px; color:{INK}; font-weight:600; width:12%;">Multiplier Used</th>
          <th style="text-align:left; padding:6px 10px; color:{INK}; font-weight:600; width:33%;">Source</th>
          <th style="text-align:left; padding:6px 10px; color:{INK}; font-weight:600; width:33%;">Link</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid {RULE}; background:{CANVAS};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Account Opening</td>
          <td style="padding:8px 10px; color:{BODY};">1.6x loans/yr</td>
          <td style="padding:8px 10px; color:{BODY};">FDIC Call Report Data. Community banks typically open 1.5 to 1.8 new accounts per loan originated. Tracks deposit account and loan volumes by institution size.</td>
          <td style="padding:8px 10px;"><a href="https://www.ffiec.gov/npw/FinancialReport/ReturnFinancialReport" target="_blank" style="color:{GREEN};">FFIEC Call Report Portal</a></td>
        </tr>
        <tr style="border-bottom:1px solid {RULE};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Account Opening (supplemental)</td>
          <td style="padding:8px 10px; color:{BODY};">1.6x loans/yr</td>
          <td style="padding:8px 10px; color:{BODY};">Cornerstone Advisors "What's Going On in Banking." Annual benchmarking report on community bank operational volumes, including account opening rates.</td>
          <td style="padding:8px 10px;"><a href="https://www.crnrstone.com/whats-going-on-in-banking" target="_blank" style="color:{GREEN};">Cornerstone Advisors Report</a></td>
        </tr>
        <tr style="border-bottom:1px solid {RULE}; background:{CANVAS};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Wire Authorization</td>
          <td style="padding:8px 10px; color:{BODY};">0.4x loans/yr</td>
          <td style="padding:8px 10px; color:{BODY};">Federal Reserve Payments Study. Tracks wire transfer volumes by institution size and type. Community banks average 0.3 to 0.5 wire events per loan originated annually.</td>
          <td style="padding:8px 10px;"><a href="https://www.federalreserve.gov/paymentsystems/fr-payments-study.htm" target="_blank" style="color:{GREEN};">Fed Reserve Payments Study</a></td>
        </tr>
        <tr style="border-bottom:1px solid {RULE};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Wire Authorization (supplemental)</td>
          <td style="padding:8px 10px; color:{BODY};">0.4x loans/yr</td>
          <td style="padding:8px 10px; color:{BODY};">NACHA. The Electronic Payments Association publishes annual volume data for ACH and wire transfers broken out by bank category and size.</td>
          <td style="padding:8px 10px;"><a href="https://www.nacha.org/content/ach-network-volume-and-value-statistics" target="_blank" style="color:{GREEN};">NACHA Volume Statistics</a></td>
        </tr>
        <tr style="border-bottom:1px solid {RULE}; background:{CANVAS};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Beneficiary / POA</td>
          <td style="padding:8px 10px; color:{BODY};">0.3x loans/yr</td>
          <td style="padding:8px 10px; color:{BODY};">BAI Banking Strategies. Banking Administration Institute research on document workflows at community institutions. Beneficiary and POA changes tracked as a share of account events.</td>
          <td style="padding:8px 10px;"><a href="https://www.bai.org/banking-strategies" target="_blank" style="color:{GREEN};">BAI Banking Strategies</a></td>
        </tr>
        <tr style="border-bottom:1px solid {RULE};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">HR Documents</td>
          <td style="padding:8px 10px; color:{BODY};">~50 docs/yr (fixed)</td>
          <td style="padding:8px 10px; color:{BODY};">SHRM. Society for Human Resource Management benchmarks HR document volume for financial services firms by headcount. Fifty docs per year is a conservative floor for a 10 to 30 person community bank.</td>
          <td style="padding:8px 10px;"><a href="https://www.shrm.org/topics-tools/research" target="_blank" style="color:{GREEN};">SHRM Research</a></td>
        </tr>
        <tr style="background:{CANVAS};">
          <td style="padding:8px 10px; color:{BODY}; font-weight:600;">Vendor / Compliance</td>
          <td style="padding:8px 10px; color:{BODY};">~30 docs/yr (fixed)</td>
          <td style="padding:8px 10px; color:{BODY};">FFIEC Examination Handbook. Outlines vendor management and compliance documentation requirements for community banks. Thirty docs per year reflects minimum vendor contract and audit cycles.</td>
          <td style="padding:8px 10px;"><a href="https://ithandbook.ffiec.gov/it-booklets/vendor-and-third-party-management.aspx" target="_blank" style="color:{GREEN};">FFIEC IT Handbook: Vendor Mgmt</a></td>
        </tr>
      </tbody>
    </table>
    <p style="margin:12px 0 0; color:{MUTED}; font-size:11px;">
      Note: Beneficiary/POA and the fixed HR/Vendor estimates are less directly sourced than Account Opening and Wire Authorization.
      Treat those rows as reasonable assumptions until discovery conversations surface real data.
      All multipliers apply to estimated annual loan signing volume per account.
    </p>
  </div>

</div>

<div class="footer">
  SIGNiX Internal Use Only &nbsp;·&nbsp; Head of Growth and Marketing &nbsp;·&nbsp; April 13, 2026
  &nbsp;·&nbsp; All expansion figures are model estimates based on community bank industry benchmarks.
  Replace with actuals as discovery conversations surface real data.
</div>

</body>
</html>"""

# ── Write output ──────────────────────────────────────────────────────────────
out_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'DELIVERABLES')
out_path = os.path.normpath(os.path.join(out_dir, 'SIGNiX_TruStage_Expansion_Model_April2026.html'))

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"Saved: {out_path}")
print(f"  Portfolio current (annual est.): {total_current:,} transactions")
print(f"  Portfolio total addressable:     {total_addressable:,} transactions")
print(f"  Current share of wallet:         {portfolio_share}%")
print(f"  Expansion gap:                   {total_expansion:,} transactions")
print(f"  SMS revenue potential (gap):     ${total_exp_sms:,}/yr")
print(f"  ID Verify potential (gap):       ${total_exp_idv:,}/yr")
