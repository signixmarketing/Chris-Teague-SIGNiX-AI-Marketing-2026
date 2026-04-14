"""
SIGNiX TruStage Portfolio Dashboard Builder — Rev 2 (Karl Matthews feedback Apr 11, 2026)
Generates: PROJECT-DOCS/DELIVERABLES/SIGNiX_TruStage_Dashboard_April2026.html
Source data: S 2026/SIGNiX-Reference/Trustage-Signix Transaction-Sales Reporting 03-31-2026 v2.xlsx
Run from: PROJECT-DOCS/ directory

Rev 2 changes (Karl Matthews feedback):
- Bank of Pontiac: monthly run rate framing (~100/month, $20/month SMS)
- Zero-auth accounts: monthly run rate + estimated monthly value
- Old Monroe ID Verify decline alert (Dec 16 → Jan 10 → Feb 6 → Mar 9 → Apr 1)
- API vs. MyDoX channel split — monthly trend chart + KPI
- API-with-auth vs. MyDoX-with-auth cross-view
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

FONT = dict(family='Calibri, Arial', color=BODY)

# ── Pricing ───────────────────────────────────────────────────────────────────
SMS_PRICE       = 0.25   # per OTP event (incl. retries/failures — all billed); $0.20 for select legacy accounts
ID_VERIFY_PRICE = 1.50   # Persona ID Verify per event (Jay's target product)

# ── Data period ───────────────────────────────────────────────────────────────
DATA_MONTHS = 15  # Jan 2025 – Mar 2026 (used for monthly run rate estimates)

# ── Monthly transaction data (Jan 2025 – Mar 2026) ────────────────────────────
MONTHS = [
    'Jan 25','Feb 25','Mar 25','Apr 25','May 25','Jun 25',
    'Jul 25','Aug 25','Sep 25','Oct 25','Nov 25','Dec 25',
    'Jan 26','Feb 26','Mar 26'
]

MONTHLY = {
    # Updated April 13, 2026 — sourced from billing report:
    # "Transaction and Submitter Summary 03-2026.xlsx" (authoritative source)
    # Previous values came from TruStage Excel reporting file (underreported by 232 transactions total)
    'MyDox':    [233,190,274,325,248,260,329,338,315,408,315,451, 397,468,546],
    'Hawthorn': [ 12, 17, 75, 35, 57, 81,108,144,167,245,204,241, 247,285,285],
    'Seattle':  [ 18, 37, 76,173,206,139,102, 85, 42, 43, 29, 36,  33, 59,176],
    'Integra':  [  3, 30, 42, 57, 44, 67, 59, 16, 37, 51, 53, 53,  54, 61, 53],
    'Accrue':   [  0,  0,  0,  0,  0, 17, 10, 18, 14, 17, 12, 36,  83,110, 70],
}

SOURCE_COLORS = {
    'MyDox':    GREEN,
    'Hawthorn': '#4a7a2e',
    'Seattle':  '#8ab86b',
    'Integra':  '#b5d49b',
    'Accrue':   '#d8ecc8',
}

# ── API vs. MyDoX monthly totals ──────────────────────────────────────────────
# MyDoX = TruStage's own document platform (stopgap; not the deal thesis)
# API   = Hawthorn River + Seattle Bank + Integra + Accrue (partner integrations)
# The deal premise: TruStage banking/CU partners integrate SIGNiX via API.
# MyDoX volume does not validate the deal thesis. API volume does.
MYDOX_MONTHLY = MONTHLY['MyDox']
API_MONTHLY   = [
    MONTHLY['Hawthorn'][i] + MONTHLY['Seattle'][i] +
    MONTHLY['Integra'][i]  + MONTHLY['Accrue'][i]
    for i in range(len(MONTHS))
]

q1_api   = sum(API_MONTHLY[-3:])
q1_mydox = sum(MYDOX_MONTHLY[-3:])
q1_total = q1_api + q1_mydox
api_pct  = round(q1_api / q1_total * 100) if q1_total else 0

# ── Old Monroe ID Verify monthly trend (Karl confirmed Apr 11) ────────────────
# Declining: Dec 25=16, Jan 26=10, Feb 26=6, Mar 26=9, Apr 26 (partial)=1
OLD_MONROE_IDV_MONTHS = ['Dec 25', 'Jan 26', 'Feb 26', 'Mar 26', 'Apr 26*']
OLD_MONROE_IDV_VALUES = [16, 10, 6, 9, 1]

# ── Bank of Pontiac run rate (Karl confirmed Apr 11) ─────────────────────────
PONTIAC_MONTHLY_RATE = 100  # current transactions/month
PONTIAC_SMS_MONTHLY  = round(PONTIAC_MONTHLY_RATE * SMS_PRICE, 2)
PONTIAC_IDV_MONTHLY  = round(PONTIAC_MONTHLY_RATE * ID_VERIFY_PRICE, 2)

# ── Per-account data ──────────────────────────────────────────────────────────
# Columns: name, transactions, sms, id_verify, kba_only, select_account, source
# source: 'API' = partner integration channel; 'MyDoX' = TruStage document platform
# Note: per-account source tagging is an approximation based on integration data.
# Accounts transacting via Hawthorn River, Seattle Bank, Integra, or Accrue = API.
# Accounts transacting primarily via TruStage MyDoX portal = MyDoX.
# Full account-level source attribution requires CTO telemetry data.

ACCOUNTS = [
    # name                          trans  sms   idv  kba  select  source
    ('Greenfield Banking Co.',        175,  470,   0,   1, False, 'API'),
    ('Merchants National Bank',       298,  474,   0,   0, False, 'API'),
    ('Bank of Old Monroe',            376,  490,  91,  38, False, 'API'),
    ("Peoples Bank, Pratt KS",        107,  199,   0,   0, False, 'API'),
    ('Peoples Bank Brownstown',       178,  240,   0,   0, False, 'API'),
    ('Clinton Bank',                  253,  336,   0,   0, False, 'API'),
    ('State Bank of Cherry',          142,  202,   0,   0, False, 'API'),
    ('Blue Grass Valley Bank',         70,  138,   0,   1, False, 'API'),
    ("Citizen's Bank of Enterprise",  193,  244,   0,   0, False, 'API'),
    ('Patterson State Bank',           71,   97,   0,   0, False, 'API'),
    ('Halstead Bank',                  35,   29,   0,  19, False, 'API'),
    ('BankTennessee',                 165,  119,   0,   0, False, 'API'),
    ('State Bank of SW Missouri',      13,   18,   0,   0, False, 'API'),
    ('First State Bank of BW, TX',     39,   35,   0,   0, False, 'API'),
    ('First State Bank',               11,   14,   0,   0, False, 'API'),
    ('Danville State Savings Bank',    37,   29,   0,   0, False, 'API'),
    ('Bank of Pontiac',              2158,  699,   0,   0, False, 'MyDoX'),
    ('EntreBank',                     617,  250,   1,  25, False, 'API'),
    ('Farmers & Merchants Bank',       66,   11,   0,   3, False, 'API'),
    ('FBT Bank & Mortgage',           526,   63,   0,   1, False, 'MyDoX'),
    ('First Natl Bank of Aspermont',  289,   13,   1,   1, False, 'API'),
    ('Bank of Frankewing',             43,    3,   0,   0, False, 'API'),
    ('Metro Bank',                     78,    1,   0,   0, False, 'MyDoX'),
    ('Commercial Bank of TX',         610,    4,   0,   0, False, 'MyDoX'),
    ('Bank of South Carolina',          9,    3,   0,   0, False, 'API'),
    ('Greenville Federal Bank',       403,    0,   0,   0, False, 'MyDoX'),
    ('Heritage Bank',                  19,    0,   0,   0, False, 'API'),
    ('TS Hilton Grand Vacations',      57,    0,   0,   0, False, 'MyDoX'),
    ('BTC Bank',                       23,    0,   0,   0, False, 'API'),
    ('Bank of Commerce',               22,    0,   0,   0, False, 'API'),
    ("Citizen's Guaranty Bank",         7,    0,   0,   0, False, 'API'),
    ('Metamora State Bank',             4,    0,   0,   0, False, 'API'),
    ('RiverHills Bank',                 3,    0,   0,   0, False, 'API'),
    ('Union Savings Bank',              2,    0,   0,   0, False, 'API'),
    ('Farmers Bank',                    3,    0,   0,   0, False, 'API'),
    ('Northeast Bank',                  1,    0,   0,   0, False, 'API'),
    # Select accounts (separate billing structure)
    ('MECE Credit Union *',          3916,    0,   0,   0,  True, 'API'),
    ('Rural King (Seattle Bk.) *',   1681,    0,   5,   0,  True, 'API'),
    ('TruStage Internal *',           846,    3,   0,   0,  True, 'MyDoX'),
]

# ── Helper: compute auth rate ─────────────────────────────────────────────────
def auth_rate(trans, sms, idv, kba):
    total_auth = sms + idv + kba
    return (total_auth / trans) if trans else 0

# ── KPI totals ────────────────────────────────────────────────────────────────
all_trans = sum(a[1] for a in ACCOUNTS)
all_sms   = sum(a[2] for a in ACCOUNTS)
all_idv   = sum(a[3] for a in ACCOUNTS)
all_kba   = sum(a[4] for a in ACCOUNTS)

# Exclude select accounts for "managed portfolio" rate
managed   = [a for a in ACCOUNTS if not a[5] and a[1]]
mgd_trans = sum(a[1] for a in managed)
mgd_sms   = sum(a[2] for a in managed)
mgd_idv   = sum(a[3] for a in managed)
mgd_kba   = sum(a[4] for a in managed)
mgd_rate  = (mgd_sms + mgd_idv + mgd_kba) / mgd_trans if mgd_trans else 0

zero_auth = [a for a in ACCOUNTS if not a[5] and a[1] and
             (a[2] + a[3] + a[4]) == 0]
near_zero = [a for a in ACCOUNTS if not a[5] and a[1] and
             auth_rate(a[1], a[2], a[3], a[4]) < 0.05 and a[1] >= 10]

sms_rev = all_sms * SMS_PRICE
idv_rev = all_idv * ID_VERIFY_PRICE

# Annual pace (Q1 2026 × 4)
q1_2026     = sum(MONTHLY[s][-3] + MONTHLY[s][-2] + MONTHLY[s][-1] for s in MONTHLY)
annual_pace = q1_2026 * 4

# ── Zero-auth monthly run rates ───────────────────────────────────────────────
zero_auth_monthly = []
for a in zero_auth:
    name, trans, sms, idv, kba, sel, src = a
    monthly_rate    = round(trans / DATA_MONTHS, 1)
    monthly_sms_val = round(monthly_rate * SMS_PRICE, 2)
    monthly_idv_val = round(monthly_rate * ID_VERIFY_PRICE, 2)
    zero_auth_monthly.append((name, trans, monthly_rate, monthly_sms_val, monthly_idv_val, src))
zero_auth_monthly.sort(key=lambda x: x[1], reverse=True)

total_zero_monthly_sms = round(sum(r[3] for r in zero_auth_monthly), 2)
total_zero_monthly_idv = round(sum(r[4] for r in zero_auth_monthly), 2)

# ── API vs. MyDoX account-level totals ───────────────────────────────────────
api_accounts  = [a for a in managed if a[6] == 'API']
mydox_accounts = [a for a in managed if a[6] == 'MyDoX']

api_trans  = sum(a[1] for a in api_accounts)
mydox_trans = sum(a[1] for a in mydox_accounts)

api_auth   = sum(a[2] + a[3] + a[4] for a in api_accounts)
mydox_auth  = sum(a[2] + a[3] + a[4] for a in mydox_accounts)

api_auth_rate   = round(api_auth / api_trans * 100, 1) if api_trans else 0
mydox_auth_rate  = round(mydox_auth / mydox_trans * 100, 1) if mydox_trans else 0

# ── Chart helpers ─────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=FONT,
)

def chart_html(fig, height=320):
    fig.update_layout(height=height)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={'responsive': True})

# ── Chart 1: Monthly Transaction Volume (by source) ──────────────────────────
fig1 = go.Figure()
for src, color in SOURCE_COLORS.items():
    fig1.add_trace(go.Bar(
        name=src, x=MONTHS, y=MONTHLY[src],
        marker_color=color,
    ))
fig1.update_layout(**CHART_LAYOUT,
    barmode='stack',
    title=dict(text='Monthly Transaction Volume by Integration Source', font=dict(color=INK, size=15)),
    xaxis=dict(showgrid=False, tickangle=-30),
    yaxis=dict(gridcolor=RULE, showgrid=True, title='Transactions'),
    legend=dict(orientation='h', y=-0.25),
    margin=dict(l=50, r=20, t=50, b=80),
)

# ── Chart 2: Auth Type Breakdown (donut) ─────────────────────────────────────
fig2 = go.Figure(go.Pie(
    labels=['SMS OTP', 'ID Verify (Persona)', 'KBA (Questions)'],
    values=[all_sms, all_idv, all_kba - all_idv],
    hole=0.52,
    marker=dict(colors=[GREEN, DARK_GREEN, AMBER]),
    textinfo='label+percent',
    textfont=dict(size=12),
    hovertemplate='%{label}<br>Events: %{value}<br>%{percent}<extra></extra>',
))
fig2.update_layout(**CHART_LAYOUT,
    margin=dict(l=20, r=20, t=50, b=20),
    title=dict(text='Authentication Type Breakdown', font=dict(color=INK, size=15)),
    showlegend=False,
    annotations=[dict(
        text=f'{all_sms + all_idv + all_kba:,}<br>total auth<br>events',
        x=0.5, y=0.5, font=dict(size=13, color=INK), showarrow=False
    )],
)

# ── Chart 3: Revenue Realized vs. Potential ───────────────────────────────────
rev_labels   = ['Current (Realized)', 'If All SMS ($0.25)', 'If All ID Verify ($1.50)']
rev_realized = round(sms_rev + idv_rev, 2)
rev_sms_full = round(mgd_trans * SMS_PRICE, 2)
rev_idv_full = round(mgd_trans * ID_VERIFY_PRICE, 2)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    name='Auth Revenue',
    x=rev_labels,
    y=[rev_realized, rev_sms_full, rev_idv_full],
    marker_color=[GREEN, AMBER, RED],
    text=[f'${rev_realized:,.0f}', f'${rev_sms_full:,.0f}', f'${rev_idv_full:,.0f}'],
    textposition='outside',
))
fig3.add_annotation(
    x=2, y=rev_idv_full * 1.05,
    text=f"Annual pace: ${round(annual_pace * ID_VERIFY_PRICE):,}/yr",
    showarrow=False, font=dict(size=11, color=MUTED),
    yanchor='bottom'
)
fig3.update_layout(**CHART_LAYOUT,
    title=dict(text='Authentication Revenue: Realized vs. Potential<br>'
               '<sup>Managed portfolio only (excl. select accounts)</sup>',
               font=dict(color=INK, size=14)),
    yaxis=dict(gridcolor=RULE, tickprefix='$', title='Revenue ($)'),
    xaxis=dict(showgrid=False),
    showlegend=False,
    margin=dict(l=60, r=20, t=70, b=40),
)

# ── Chart 4: Auth Tier by Account (horizontal bar) ────────────────────────────
tier_data = []
for a in ACCOUNTS:
    name, trans, sms, idv, kba, sel, src = a
    if not trans:
        continue
    total_auth = sms + idv + kba
    rate_pct   = round((total_auth / trans) * 100, 1)
    if idv > 0:
        t_color = GREEN
        t_label = 'ID Verify Active'
    elif total_auth > 0:
        t_color = AMBER
        t_label = 'SMS / KBA Only'
    else:
        t_color = RED
        t_label = 'Zero Auth'
    tier_data.append((name, trans, rate_pct, t_color, t_label, sel))

tier_data.sort(key=lambda x: x[1])

fig4 = go.Figure()
for tl, tc in [('ID Verify Active', GREEN), ('SMS / KBA Only', AMBER), ('Zero Auth', RED)]:
    subset = [(d[0], d[1], d[2]) for d in tier_data if d[4] == tl]
    if subset:
        fig4.add_trace(go.Bar(
            name=tl,
            y=[s[0] for s in subset],
            x=[s[1] for s in subset],
            orientation='h',
            marker_color=tc,
            text=[f'{s[1]:,} trans · {s[2]}% auth' for s in subset],
            textposition='outside',
            insidetextanchor='start',
        ))
fig4.update_layout(**CHART_LAYOUT,
    barmode='stack',
    height=680,
    margin=dict(l=220, r=160, t=50, b=40),
    title=dict(text='Auth Tier by Account',
               font=dict(color=INK, size=15)),
    xaxis=dict(showgrid=True, gridcolor=RULE, title='Lifetime Transactions'),
    yaxis=dict(showgrid=False, tickfont=dict(size=11)),
    legend=dict(orientation='h', y=-0.06),
)

# ── Chart 5: CSM Priority Table ───────────────────────────────────────────────
priority_rows = []
for a in ACCOUNTS:
    name, trans, sms, idv, kba, sel, src = a
    if sel or not trans:
        continue
    total_auth  = sms + idv + kba
    rate_val    = total_auth / trans
    missed      = trans - total_auth
    if missed <= 0:
        continue
    sms_upside  = round(missed * SMS_PRICE, 2)
    idv_upside  = round(trans * ID_VERIFY_PRICE - idv * ID_VERIFY_PRICE, 2)
    monthly_est = round(trans / DATA_MONTHS, 1)
    if idv > 0:
        auth_type = 'ID Verify + SMS'
    elif total_auth > 0:
        auth_type = 'SMS / KBA'
    else:
        auth_type = 'None'
    priority_rows.append((name, trans, round(rate_val * 100, 1),
                          auth_type, missed, sms_upside, idv_upside, monthly_est, src))

priority_rows.sort(key=lambda x: x[4], reverse=True)
priority_rows = priority_rows[:12]

p_names    = [r[0] for r in priority_rows]
p_trans    = [f'{r[1]:,}' for r in priority_rows]
p_rate     = [f'{r[2]}%' for r in priority_rows]
p_type     = [r[3] for r in priority_rows]
p_missed   = [f'{r[4]:,}' for r in priority_rows]
p_sms_up   = [f'${r[5]:,.2f}' for r in priority_rows]
p_idv_up   = [f'${r[6]:,.2f}' for r in priority_rows]
p_monthly  = [f'~{r[7]:.0f}/mo' for r in priority_rows]
p_source   = [r[8] for r in priority_rows]

row_colors = []
for r in priority_rows:
    if r[3] == 'None':
        row_colors.append(LIGHT_RED)
    elif r[2] < 25:
        row_colors.append(LIGHT_AMB)
    else:
        row_colors.append(WHITE)

fig5 = go.Figure(go.Table(
    header=dict(
        values=['Account', 'Channel', 'Lifetime Trans', 'Monthly Rate',
                'Auth Rate', 'Auth Type', 'SMS Uplift ($0.25)', 'ID Verify ($1.50)'],
        fill_color=INK,
        font=dict(color=WHITE, family='Calibri, Arial', size=12),
        align='left',
        height=32,
    ),
    cells=dict(
        values=[p_names, p_source, p_trans, p_monthly, p_rate, p_type, p_sms_up, p_idv_up],
        fill_color=[row_colors] * 8,
        font=dict(color=BODY, family='Calibri, Arial', size=11),
        align='left',
        height=27,
    ),
    columnwidth=[3, 1, 1.2, 1.1, 1, 1.4, 1.5, 1.6],
))
fig5.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=50, b=10),
    paper_bgcolor=WHITE,
    title=dict(text='CSM Activation Priority'
               '<br><sup>Red = zero auth · Amber = under 25% auth · Monthly Rate = est. avg transactions/month</sup>',
               font=dict(color=INK, size=14)),
)

# ── Chart 6: API vs. MyDoX Monthly Trend ─────────────────────────────────────
fig6 = go.Figure()
fig6.add_trace(go.Bar(
    name='API Integrations (partner-driven)',
    x=MONTHS, y=API_MONTHLY,
    marker_color=GREEN,
    hovertemplate='%{x}<br>API: %{y}<extra></extra>',
))
fig6.add_trace(go.Bar(
    name='MyDoX (non-API, TruStage platform)',
    x=MONTHS, y=MYDOX_MONTHLY,
    marker_color=AMBER,
    hovertemplate='%{x}<br>MyDoX: %{y}<extra></extra>',
))
fig6.update_layout(**CHART_LAYOUT,
    barmode='group',
    title=dict(
        text=f'API vs. MyDoX — Monthly Transactions<br>'
             f'<sup>Q1 2026: API {api_pct}% ({q1_api:,} trans) · MyDoX {100-api_pct}% ({q1_mydox:,} trans) · '
             f'API auth rate {api_auth_rate}% · MyDoX auth rate {mydox_auth_rate}%</sup>',
        font=dict(color=INK, size=14)),
    xaxis=dict(showgrid=False, tickangle=-30),
    yaxis=dict(gridcolor=RULE, showgrid=True, title='Transactions'),
    legend=dict(orientation='h', y=-0.28),
    margin=dict(l=50, r=20, t=70, b=90),
)

# ── Chart 7: Zero-Auth Accounts — Monthly Run Rate Table ─────────────────────
z_names    = [r[0] for r in zero_auth_monthly]
z_lifetime = [f'{r[1]:,}' for r in zero_auth_monthly]
z_monthly  = [f'~{r[2]:.0f}/mo' for r in zero_auth_monthly]
z_sms_mo   = [f'${r[3]:.2f}/mo' for r in zero_auth_monthly]
z_idv_mo   = [f'${r[4]:.2f}/mo' for r in zero_auth_monthly]
z_source   = [r[5] for r in zero_auth_monthly]

fig7 = go.Figure(go.Table(
    header=dict(
        values=['Account', 'Channel', 'Lifetime Trans', 'Est. Monthly Rate',
                'Monthly SMS Value ($0.25)', 'Monthly ID Verify Value ($1.50)'],
        fill_color=RED,
        font=dict(color=WHITE, family='Calibri, Arial', size=12),
        align='left',
        height=32,
    ),
    cells=dict(
        values=[z_names, z_source, z_lifetime, z_monthly, z_sms_mo, z_idv_mo],
        fill_color=[[LIGHT_RED] * len(zero_auth_monthly)] * 6,
        font=dict(color=BODY, family='Calibri, Arial', size=11),
        align='left',
        height=27,
    ),
    columnwidth=[3, 1, 1.3, 1.4, 1.8, 1.8],
))
fig7.update_layout(
    height=round(60 + len(zero_auth_monthly) * 30),
    margin=dict(l=10, r=10, t=60, b=10),
    paper_bgcolor=WHITE,
    title=dict(
        text=f'Zero-Auth Accounts: Monthly Revenue Opportunity<br>'
             f'<sup>Estimated monthly SMS value if activated: ${total_zero_monthly_sms:.2f}/mo · '
             f'ID Verify: ${total_zero_monthly_idv:.2f}/mo · Monthly rate = lifetime ÷ {DATA_MONTHS} months</sup>',
        font=dict(color=INK, size=14)),
)

# ── Chart 8: Old Monroe ID Verify Trend (mini line) ───────────────────────────
fig8 = go.Figure()
fig8.add_trace(go.Scatter(
    x=OLD_MONROE_IDV_MONTHS,
    y=OLD_MONROE_IDV_VALUES,
    mode='lines+markers+text',
    line=dict(color=RED, width=2),
    marker=dict(size=8, color=RED),
    text=[str(v) for v in OLD_MONROE_IDV_VALUES],
    textposition='top center',
    textfont=dict(size=12, color=INK),
    name='ID Verify Events',
    hovertemplate='%{x}: %{y} events<extra></extra>',
))
fig8.add_annotation(
    x='Apr 26*', y=1,
    text='* April partial<br>(as of Apr 11)',
    showarrow=True, arrowhead=2, ax=40, ay=-30,
    font=dict(size=10, color=MUTED),
)
fig8.update_layout(**CHART_LAYOUT,
    title=dict(
        text='Bank of Old Monroe: ID Verify Declining<br>'
             '<sup>Peak: Dec 2025 at 16 events. Apr 2026 (partial): 1 event. Needs a CSM call now.</sup>',
        font=dict(color=INK, size=14)),
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor=RULE, showgrid=True, title='ID Verify Events', rangemode='tozero'),
    showlegend=False,
    margin=dict(l=50, r=20, t=70, b=40),
)

# ── Assemble HTML ─────────────────────────────────────────────────────────────
chart1_html = chart_html(fig1, 340)
chart2_html = chart_html(fig2, 300)
chart3_html = chart_html(fig3, 300)
chart4_html = chart_html(fig4, 680)
chart5_html = chart_html(fig5, 420)
chart6_html = chart_html(fig6, 340)
chart7_html = chart_html(fig7, round(60 + len(zero_auth_monthly) * 30))
chart8_html = chart_html(fig8, 280)

zero_names = ', '.join(a[0].replace(' *','') for a in zero_auth)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>SIGNiX TruStage Portfolio Dashboard — April 2026</title>
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
    .three-col {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }}
    .chart-card, .full-card {{
      background: {WHITE}; border: 1px solid {RULE};
      border-radius: 8px; padding: 4px 4px 0; overflow: hidden;
    }}
    .alerts {{ display: flex; flex-direction: column; gap: 10px; margin: 18px 0 8px; }}
    .alert {{
      background: {WHITE}; border-left: 4px solid {AMBER};
      border-radius: 4px; padding: 12px 16px;
      font-size: 13px; line-height: 1.5;
      display: flex; gap: 10px; align-items: flex-start;
    }}
    .alert-icon {{ font-size: 16px; flex-shrink: 0; }}
    .note-box {{
      background: {WHITE}; border: 1px solid {RULE};
      border-radius: 6px; padding: 14px 18px; font-size: 12px;
      color: {MUTED}; line-height: 1.7; margin-top: 8px;
    }}
    .footer {{
      text-align: center; padding: 20px;
      font-size: 11px; color: {MUTED};
      border-top: 1px solid {RULE}; margin-top: 32px;
    }}
    @media (max-width: 900px) {{
      .kpi-row, .two-col, .three-col {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 600px) {{
      .kpi-row, .two-col, .three-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <h1><span>SIGNiX</span> TruStage Portfolio Dashboard</h1>
    <div style="font-size:13px; color:{MUTED}; margin-top:4px;">
      Transaction &amp; Authentication Analysis &nbsp;·&nbsp; Jan 2025 – Mar 2026 &nbsp;·&nbsp; Updated April 13, 2026
    </div>
  </div>
  <div class="header-meta">
    Prepared by Chris Teague<br>
    Head of Growth and Marketing<br>
    Updated April 11, 2026
  </div>
</div>

<div class="container">

  <!-- KPI Scorecard -->
  <div class="section-title">Portfolio Scorecard</div>
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-value" style="color:{GREEN};">{all_trans:,}</div>
      <div class="kpi-label">Total Transactions</div>
      <div class="kpi-sub">Jan 2025 – Mar 2026 · All sources</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{GREEN};">{round(mgd_rate*100,1)}%</div>
      <div class="kpi-label">Managed Portfolio Auth Rate</div>
      <div class="kpi-sub">Excl. select accounts (MECE, Rural King)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{AMBER};">{api_pct}%</div>
      <div class="kpi-label">API Share (Q1 2026)</div>
      <div class="kpi-sub">{q1_api:,} API vs {q1_mydox:,} MyDoX transactions</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{GREEN};">{all_sms:,}</div>
      <div class="kpi-label">SMS OTP Events</div>
      <div class="kpi-sub">${sms_rev:.2f} realized · $0.25/event</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value" style="color:{RED};">{len(zero_auth)}</div>
      <div class="kpi-label">Accounts at Zero Auth</div>
      <div class="kpi-sub">~${total_zero_monthly_sms:.2f}/mo SMS potential if activated</div>
    </div>
  </div>

  <!-- Key Findings -->
  <div class="section-title">Key Findings</div>
  <div class="alerts">
    <div class="alert" style="border-left-color:{RED};">
      <span class="alert-icon">⚠️</span>
      <span><strong>Bank of Pontiac is the top priority.</strong>
      It runs ~{PONTIAC_MONTHLY_RATE} transactions per month at 32% auth rate.
      That leaves over 1,400 unauthenticated events on the table.
      SMS alone would add ${PONTIAC_SMS_MONTHLY:.2f}/month. ID Verify would add ${PONTIAC_IDV_MONTHLY:.2f}/month.
      One call with Mike could move this account from 32% to 80%+.</span>
    </div>
    <div class="alert" style="border-left-color:{RED};">
      <span class="alert-icon">📉</span>
      <span><strong>Bank of Old Monroe is losing ground.</strong>
      This is our flagship ID Verify account at $1.50 per event.
      Usage peaked at 16 events in December. It's down to 1 so far in April.
      Mike needs to call this account now.</span>
    </div>
    <div class="alert" style="border-left-color:{RED};">
      <span class="alert-icon">⚠️</span>
      <span><strong>{len(zero_auth)} accounts are signing documents with no authentication at all.</strong>
      Combined: {sum(a[1] for a in zero_auth):,} lifetime transactions and $0 in auth revenue.
      Turning on SMS for all of them would add ${total_zero_monthly_sms:.2f}/month.
      Commercial Bank of TX has 610 more transactions at 0.7% auth — effectively zero too.
      See the table below for each account's monthly run rate.</span>
    </div>
    <div class="alert" style="border-left-color:{AMBER};">
      <span class="alert-icon">🔌</span>
      <span><strong>API is at {api_pct}% of Q1 2026 volume. MyDoX is at {100-api_pct}%.</strong>
      MyDoX was a bridge when API adoption was slow. The TruStage deal was built on API.
      API accounts authenticate at {api_auth_rate}%. MyDoX accounts authenticate at {mydox_auth_rate}%.
      The auth gap lives in MyDoX. See the channel mix chart below.</span>
    </div>
    <div class="alert" style="border-left-color:{GREEN};">
      <span class="alert-icon">📈</span>
      <span><strong>Volume is growing fast.</strong>
      Q1 2026 is the strongest quarter on record at {q1_2026:,} transactions.
      At this pace, 2026 will reach ~{annual_pace:,} transactions total.
      That's {round(annual_pace/6552*100-100)}% above 2025. More volume means more auth opportunity every month.</span>
    </div>
  </div>

  <!-- Monthly Volume -->
  <div class="section-title">Monthly Transaction Volume by Source</div>
  <div class="full-card">{chart1_html}</div>

  <!-- Auth Breakdown + Revenue -->
  <div class="section-title">Authentication Analysis</div>
  <div class="two-col">
    <div class="chart-card">{chart2_html}</div>
    <div class="chart-card">{chart3_html}</div>
  </div>

  <!-- API vs MyDoX Channel Mix -->
  <div class="section-title">Channel Mix — API vs. MyDoX (Deal Thesis Health)</div>
  <div class="full-card">{chart6_html}</div>
  <div class="note-box">
    The TruStage deal was built on API. Banks and credit unions embed SIGNiX directly into their workflows.
    MyDoX was a bridge when API adoption was slow. It still accounts for nearly half of volume.
    API accounts authenticate at <strong>{api_auth_rate}%</strong>. MyDoX accounts authenticate at <strong>{mydox_auth_rate}%</strong>.
    Growing the API share is the right signal to watch.
    Account-level source attribution is an estimate. Exact channel data requires a CTO report.
  </div>

  <!-- Old Monroe Decline -->
  <div class="section-title">ID Verify Proof-of-Concept — Bank of Old Monroe Trend</div>
  <div class="full-card">{chart8_html}</div>

  <!-- Auth Tier by Account -->
  <div class="section-title">Authentication Tier by Account</div>
  <div class="full-card">{chart4_html}</div>

  <div class="note-box">
    🟢 <strong>ID Verify Active:</strong> biometric verification in use ($1.50/event).
    &nbsp;·&nbsp; 🟡 <strong>SMS / KBA Only:</strong> multi-factor auth active, not yet on ID Verify.
    &nbsp;·&nbsp; 🔴 <strong>Zero Auth:</strong> no identity verification on any transaction.
    &nbsp;·&nbsp; <strong>* Select accounts</strong> have separate billing. SMS count includes retries and failed attempts.
  </div>

  <!-- Zero-Auth Monthly Run Rate Table -->
  <div class="section-title">Zero-Auth Accounts — Monthly Revenue Opportunity</div>
  <div class="full-card">{chart7_html}</div>
  <div class="note-box">
    Monthly rate = lifetime transactions divided by {DATA_MONTHS} months (Jan 2025 – Mar 2026).
    Newer accounts may run higher than shown. SMS and ID Verify values are estimates at current run rate.
  </div>

  <!-- CSM Priority Table -->
  <div class="section-title">CSM Activation Priority</div>
  <div class="full-card">{chart5_html}</div>

  <div class="note-box">
    <strong>Monthly Rate:</strong> lifetime transactions divided by {DATA_MONTHS} months.
    <strong>SMS Uplift:</strong> added revenue if unauthenticated events switched to SMS at $0.25.
    <strong>ID Verify:</strong> added revenue if all transactions used ID Verify at $1.50.
    Ranked by unauthenticated volume. Red = zero auth. Amber = under 25% auth.
    Select accounts excluded (MECE, Rural King, TruStage Internal — separate billing).
  </div>

</div>

<div class="footer">
  SIGNiX Internal Use Only &nbsp;·&nbsp;
  Transaction volume: Transaction and Submitter Summary 03-2026.xlsx (billing report, authoritative source) &nbsp;·&nbsp;
  Per-account auth data: TruStage–SIGNiX Transaction-Sales Reporting 03-31-2026 v2.xlsx &nbsp;·&nbsp;
  Authentication pricing: SMS $0.25/event (standard; $0.20 for select legacy accounts) · ID Verify $1.50/event &nbsp;·&nbsp;
  Rev 4 — Per-account data validated against billing report (columns AH-BA); Northeast Bank added; all accounts confirmed April 13, 2026
</div>

</body>
</html>"""

# ── Write output ──────────────────────────────────────────────────────────────
out_dir  = os.path.join(os.path.dirname(__file__), '..', 'DELIVERABLES')
out_path = os.path.join(out_dir, 'SIGNiX_TruStage_Dashboard_April2026.html')
out_path = os.path.normpath(out_path)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"✓ Dashboard written to: {out_path}")
print(f"  Total transactions:    {all_trans:,}")
print(f"  Managed auth rate:     {round(mgd_rate*100,1)}%")
print(f"  API share (Q1 2026):   {api_pct}% ({q1_api} trans)")
print(f"  MyDoX share (Q1 2026): {100-api_pct}% ({q1_mydox} trans)")
print(f"  API auth rate:         {api_auth_rate}%")
print(f"  MyDoX auth rate:       {mydox_auth_rate}%")
print(f"  ID Verify events:      {all_idv} (${idv_rev:.2f})")
print(f"  SMS OTP events:        {all_sms:,} (${sms_rev:.2f})")
print(f"  Zero-auth accounts:    {len(zero_auth)} (~${total_zero_monthly_sms:.2f}/mo SMS potential)")
print(f"  2026 annual pace:      ~{annual_pace:,} transactions")
