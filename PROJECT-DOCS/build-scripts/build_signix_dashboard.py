#!/usr/bin/env python3
"""
SIGNiX Marketing Dashboard Builder
Generates a self-contained HTML dashboard from Google Ads + HubSpot exports.
Run with: python3 "PROJECT-DOCS/build-scripts/build_signix_dashboard.py"
Re-run any time to refresh with new CSV exports.
"""

import csv
import os
import shutil
from datetime import datetime

import plotly.graph_objects as go
import plotly.offline as po

# ── Data file paths ────────────────────────────────────────────────────────────
# Update DATA_DIR if you move files from Downloads to the project folder.
DATA_DIR = os.path.expanduser("~/Downloads")

F_CAMPAIGNS   = os.path.join(DATA_DIR, "Campaign report.csv")
F_ADGROUPS    = os.path.join(DATA_DIR, "Ad group report.csv")
F_KEYWORDS    = os.path.join(DATA_DIR, "Search keyword report.csv")
F_DAILY_CLICK = os.path.join(DATA_DIR, "Time_series_chart(2026.03.09-2026.04.07) (1).csv")
F_DAILY_CONV  = os.path.join(DATA_DIR, "Time_series_chart(2026.03.09-2026.04.07) (2).csv")
F_HUBSPOT     = os.path.join(DATA_DIR, "hubspot-core-report-custom-contacts-report-2026-04-08.csv")
F_LINKEDIN    = os.path.join(DATA_DIR, "signix_content_1775825335754.xls")

# ── Brand tokens ───────────────────────────────────────────────────────────────
GREEN      = "#6da34a"
INK        = "#2e3440"
BODY       = "#545454"
MUTED      = "#6b7280"
WHITE      = "#ffffff"
CANVAS     = "#f8fafb"
RULE       = "#d8dee9"
RED        = "#e05252"
AMBER      = "#e0a252"
DARK_GREEN = "#4a7a2e"

BUSINESS_HOURS = range(9, 17)   # 9 AM – 4:59 PM; hour 17 = 5 PM start = off-hours

# ── Helpers ────────────────────────────────────────────────────────────────────
def _clean(val):
    """Strip commas, spaces, percent signs and cast to float. Return 0 on fail."""
    try:
        return float(str(val).replace(",", "").replace("%", "").replace("$", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def read_tsv_utf16(path, skip_rows=2):
    """Read a UTF-16 TSV Google Ads export. Returns (header, data_rows).
    Filters out Total/summary rows that Google Ads appends at the bottom."""
    with open(path, encoding="utf-16") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))
    header = rows[skip_rows]
    data   = [r for r in rows[skip_rows + 1:]
              if len(r) > 3
              and r[1].strip()                        # Campaign/name column must have a value
              and r[1].strip() not in ("--", " --")  # Skip "Total" aggregate rows
              and not r[0].startswith("Total")]       # Skip explicit Total rows
    return header, data


def read_csv_utf8(path):
    """Read a plain UTF-8-sig CSV. Returns (header, data_rows)."""
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def chart_div(fig):
    """Return a Plotly chart as an HTML <div> string (no JS — relies on CDN load)."""
    return po.plot(fig, include_plotlyjs=False, output_type="div")


# ── Load data ──────────────────────────────────────────────────────────────────
# Campaigns
camp_hdr, camp_rows = read_tsv_utf16(F_CAMPAIGNS)
ci = {k: camp_hdr.index(k) for k in
      ["Campaign", "Impr.", "Clicks", "Cost", "Conversions", "Avg. CPC", "Cost / conv.",
       "Conv. rate", "Interaction rate"]}

campaigns = []
for row in camp_rows:
    if len(row) <= max(ci.values()):
        continue
    campaigns.append({
        "name":      row[ci["Campaign"]].replace("(Arcb) ", ""),
        "impr":      _clean(row[ci["Impr."]]),
        "clicks":    _clean(row[ci["Clicks"]]),
        "cost":      _clean(row[ci["Cost"]]),
        "conv":      _clean(row[ci["Conversions"]]),
        "cpc":       _clean(row[ci["Avg. CPC"]]),
        "cpl":       _clean(row[ci["Cost / conv."]]),
        "conv_rate": _clean(row[ci["Conv. rate"]]),
        "ctr":       _clean(row[ci["Interaction rate"]]),
    })

total_spend = sum(c["cost"]  for c in campaigns)
total_clicks = sum(c["clicks"] for c in campaigns)
total_conv   = sum(c["conv"]   for c in campaigns)
avg_cpc      = total_spend / total_clicks if total_clicks else 0
avg_cpl      = total_spend / total_conv   if total_conv else 0

# Ad groups (hourly)
ag_hdr, ag_rows_raw = read_tsv_utf16(F_ADGROUPS)
ag_hdr_full, ag_all = read_tsv_utf16(F_ADGROUPS, skip_rows=2)

# Rebuild: include rows with a non-empty campaign column
with open(F_ADGROUPS, encoding="utf-16") as fh:
    all_ag_rows = list(csv.reader(fh, delimiter="\t"))

ag_header   = all_ag_rows[2]
ag_ci       = {k: ag_header.index(k) for k in
               ["Hour of the day", "Ad group", "Campaign", "Clicks", "Cost",
                "Conversions", "Impr."]}

by_hour   = {}
by_adgroup = {}

for row in all_ag_rows[3:]:
    if len(row) <= max(ag_ci.values()):
        continue
    campaign = row[ag_ci["Campaign"]].strip()
    if not campaign or campaign.startswith("Total"):
        continue
    try:
        h    = int(row[ag_ci["Hour of the day"]])
        grp  = row[ag_ci["Ad group"]].strip()
        clk  = _clean(row[ag_ci["Clicks"]])
        cost = _clean(row[ag_ci["Cost"]])
        conv = _clean(row[ag_ci["Conversions"]])
        impr = _clean(row[ag_ci["Impr."]])

        if h not in by_hour:
            by_hour[h] = {"clicks": 0, "cost": 0.0}
        by_hour[h]["clicks"] += clk
        by_hour[h]["cost"]   += cost

        key = f"{campaign.replace('(Arcb) ', '')} — {grp}"
        if key not in by_adgroup:
            by_adgroup[key] = {"clicks": 0, "cost": 0.0, "conv": 0.0, "impr": 0}
        by_adgroup[key]["clicks"] += clk
        by_adgroup[key]["cost"]   += cost
        by_adgroup[key]["conv"]   += conv
        by_adgroup[key]["impr"]   += impr
    except (ValueError, IndexError):
        continue

biz_cost  = sum(v["cost"]   for h, v in by_hour.items() if h in BUSINESS_HOURS)
off_cost  = sum(v["cost"]   for h, v in by_hour.items() if h not in BUSINESS_HOURS)
biz_click = sum(v["clicks"] for h, v in by_hour.items() if h in BUSINESS_HOURS)
off_click = sum(v["clicks"] for h, v in by_hour.items() if h not in BUSINESS_HOURS)
off_pct   = off_cost / (biz_cost + off_cost) * 100 if (biz_cost + off_cost) else 0

# Keywords
kw_hdr, kw_rows = read_tsv_utf16(F_KEYWORDS)
kw_ci = {k: kw_hdr.index(k) for k in
         ["Keyword", "Campaign", "Ad group", "Clicks", "Cost", "Conversions", "Impr.",
          "Avg. CPC"]}

keywords = []
for row in kw_rows:
    if len(row) <= max(kw_ci.values()):
        continue
    kw = row[kw_ci["Keyword"]].strip()
    if not kw or kw.startswith("Total"):
        continue
    keywords.append({
        "kw":   kw,
        "camp": row[kw_ci["Campaign"]].replace("(Arcb) ", ""),
        "grp":  row[kw_ci["Ad group"]],
        "clk":  _clean(row[kw_ci["Clicks"]]),
        "cost": _clean(row[kw_ci["Cost"]]),
        "conv": _clean(row[kw_ci["Conversions"]]),
        "impr": _clean(row[kw_ci["Impr."]]),
        "cpc":  _clean(row[kw_ci["Avg. CPC"]]),
    })

keywords.sort(key=lambda x: -x["clk"])
top_kws  = keywords[:12]
zero_kws = [k for k in keywords if k["conv"] == 0 and k["cost"] > 20]
zero_waste = sum(k["cost"] for k in zero_kws)

# HubSpot leads
def parse_response_mins(val):
    """Parse HH:MM:SS response time string into float minutes. Returns None if blank."""
    if not val or not str(val).strip():
        return None
    try:
        parts = str(val).strip().split(":")
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1]) + float(parts[2]) / 60
    except (ValueError, IndexError):
        pass
    return None

def fmt_duration(mins):
    """Format minutes as human-readable string."""
    if mins is None:
        return "No follow-up"
    if mins < 60:
        return f"{mins:.0f} min"
    elif mins < 1440:
        return f"{mins/60:.1f} hrs"
    else:
        return f"{mins/1440:.1f} days"

hs_leads = []
try:
    with open(F_HUBSPOT, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            mins = parse_response_mins(row.get("Lead response time", ""))
            hs_leads.append({
                "name":    f"{row.get('First Name','').strip()} {row.get('Last Name','').strip()}".strip(),
                "company": row.get("Company Name", "").strip() or "—",
                "source":  row.get("Original Source Data 1", "").strip(),
                "stage":   row.get("Lifecycle Stage", "").strip(),
                "mins":    mins,
                "label":   fmt_duration(mins),
            })
except FileNotFoundError:
    pass

hs_timed      = [l for l in hs_leads if l["mins"] is not None]
hs_no_followup = [l for l in hs_leads if l["mins"] is None or l["mins"] > 1440]
hs_total      = len(hs_leads)
avg_resp_mins = sum(l["mins"] for l in hs_timed) / len(hs_timed) if hs_timed else 0
ct_5min       = sum(1 for l in hs_leads if l["mins"] is not None and l["mins"] <= 5)
ct_10min      = sum(1 for l in hs_leads if l["mins"] is not None and l["mins"] <= 10)

# Daily trends
_, daily_clicks_rows = read_csv_utf8(F_DAILY_CLICK)
_, daily_conv_rows   = read_csv_utf8(F_DAILY_CONV)

dates  = [r[0] for r in daily_clicks_rows if len(r) >= 2]
d_clk  = [_clean(r[1]) for r in daily_clicks_rows if len(r) >= 2]
d_conv = [_clean(r[1]) for r in daily_conv_rows   if len(r) >= 2]

# ── Build charts ───────────────────────────────────────────────────────────────

# Chart 1 — Campaign grouped bar
fig_camp = go.Figure()
metrics = ["clicks", "conv"]
labels  = ["Clicks", "Conversions"]
colors  = [GREEN, DARK_GREEN]

for i, (m, label, color) in enumerate(zip(metrics, labels, colors)):
    fig_camp.add_trace(go.Bar(
        name=label,
        x=[c["name"] for c in campaigns],
        y=[c[m] for c in campaigns],
        marker_color=color,
        text=[f"{c[m]:.0f}" for c in campaigns],
        textposition="outside",
    ))

fig_camp.add_trace(go.Bar(
    name="Cost ($)",
    x=[c["name"] for c in campaigns],
    y=[c["cost"] for c in campaigns],
    marker_color=MUTED,
    text=[f"${c['cost']:,.0f}" for c in campaigns],
    textposition="outside",
))

fig_camp.update_layout(
    title=dict(text="Campaign Performance", font=dict(size=15, color=INK)),
    barmode="group",
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(family="Calibri, Arial", color=BODY),
    legend=dict(orientation="h", y=-0.15),
    yaxis=dict(showgrid=True, gridcolor=RULE),
    margin=dict(t=50, b=60, l=40, r=20),
    height=320,
)

# Chart 2 — Daily clicks + conversions
fig_daily = go.Figure()
fig_daily.add_trace(go.Scatter(
    x=dates, y=d_clk,
    name="Clicks",
    mode="lines+markers",
    line=dict(color=GREEN, width=2),
    marker=dict(size=4),
    fill="tozeroy",
    fillcolor="rgba(109,163,74,0.08)",
))
fig_daily.add_trace(go.Scatter(
    x=dates, y=d_conv,
    name="Conversions",
    mode="lines+markers",
    line=dict(color=DARK_GREEN, width=2),
    marker=dict(size=5),
    yaxis="y2",
))
fig_daily.update_layout(
    title=dict(text="Daily Clicks & Conversions", font=dict(size=15, color=INK)),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(family="Calibri, Arial", color=BODY),
    xaxis=dict(showgrid=False, tickangle=-30, nticks=15),
    yaxis=dict(title="Clicks", showgrid=True, gridcolor=RULE),
    yaxis2=dict(title="Conversions", overlaying="y", side="right",
                showgrid=False, range=[0, max(d_conv)*6 if d_conv else 2]),
    legend=dict(orientation="h", y=-0.2),
    margin=dict(t=50, b=60, l=50, r=50),
    height=320,
)

# Chart 3 — Hourly clicks bar (colored by business / off-hours)
sorted_hours = sorted(by_hour.keys())
hour_labels  = [f"{h:02d}:00" for h in sorted_hours]
hour_clicks  = [by_hour[h]["clicks"] for h in sorted_hours]
hour_costs   = [by_hour[h]["cost"]   for h in sorted_hours]
hour_colors  = [GREEN if h in BUSINESS_HOURS else RED for h in sorted_hours]

fig_hourly = go.Figure()
fig_hourly.add_trace(go.Bar(
    x=hour_labels,
    y=hour_clicks,
    marker_color=hour_colors,
    name="Clicks",
    customdata=[[f"${hour_costs[i]:.2f}"] for i in range(len(sorted_hours))],
    hovertemplate="<b>%{x}</b><br>Clicks: %{y}<br>Cost: %{customdata[0]}<extra></extra>",
))

# Shade annotation
fig_hourly.add_vrect(
    x0="09:00", x1="16:00",
    fillcolor="rgba(109,163,74,0.06)",
    layer="below", line_width=0,
    annotation_text="9 AM – 5 PM target window",
    annotation_position="top left",
    annotation_font=dict(color=GREEN, size=11),
)

fig_hourly.update_layout(
    title=dict(
        text=f"Clicks by Hour of Day — {off_pct:.0f}% of spend (${off_cost:,.0f}) ran outside business hours",
        font=dict(size=14, color=INK)
    ),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(family="Calibri, Arial", color=BODY),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor=RULE),
    showlegend=False,
    margin=dict(t=60, b=40, l=40, r=20),
    height=300,
)

# Chart 4 — Ad group performance (cost bar)
ag_sorted = sorted(by_adgroup.items(), key=lambda x: -x[1]["cost"])[:8]
ag_names  = [k.replace(" — ", "\n") for k, _ in ag_sorted]
ag_costs  = [v["cost"]   for _, v in ag_sorted]
ag_convs  = [v["conv"]   for _, v in ag_sorted]

fig_ag = go.Figure()
fig_ag.add_trace(go.Bar(
    x=ag_names,
    y=ag_costs,
    marker_color=GREEN,
    name="Cost",
    text=[f"${c:,.0f}" for c in ag_costs],
    textposition="outside",
))
fig_ag.add_trace(go.Scatter(
    x=ag_names,
    y=ag_convs,
    mode="markers+text",
    marker=dict(size=12, color=DARK_GREEN, symbol="diamond"),
    text=[f"{int(c)}" for c in ag_convs],
    textposition="top center",
    name="Conversions",
    yaxis="y2",
))
fig_ag.update_layout(
    title=dict(text="Ad Group Performance (Cost + Conversions)", font=dict(size=15, color=INK)),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(family="Calibri, Arial", color=BODY, size=10),
    xaxis=dict(showgrid=False),
    yaxis=dict(title="Cost ($)", showgrid=True, gridcolor=RULE),
    yaxis2=dict(title="Conversions", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", y=-0.25),
    margin=dict(t=50, b=90, l=50, r=50),
    height=340,
)

# Chart 5 — Top keywords table
kw_fig = go.Figure(data=[go.Table(
    columnwidth=[3, 1.5, 0.8, 0.8, 0.8, 0.8],
    header=dict(
        values=["Keyword", "Ad Group", "Clicks", "Cost", "Conv.", "Avg. CPC"],
        fill_color=INK,
        font=dict(color=WHITE, size=12, family="Calibri, Arial"),
        align="left",
        height=30,
    ),
    cells=dict(
        values=[
            [k["kw"]  for k in top_kws],
            [k["grp"] for k in top_kws],
            [int(k["clk"])  for k in top_kws],
            [f"${k['cost']:.2f}" for k in top_kws],
            [int(k["conv"]) for k in top_kws],
            [f"${k['cpc']:.2f}" for k in top_kws],
        ],
        fill_color=[[CANVAS if i % 2 == 0 else WHITE for i in range(len(top_kws))]],
        font=dict(color=BODY, size=11, family="Calibri, Arial"),
        align="left",
        height=26,
    ),
)])
kw_fig.update_layout(
    title=dict(text="Top Keywords by Clicks", font=dict(size=15, color=INK)),
    paper_bgcolor=WHITE,
    margin=dict(t=50, b=10, l=10, r=10),
    height=420,
)

# Chart 6 — HubSpot response time horizontal bar
if hs_leads:
    hs_sorted  = sorted(hs_timed, key=lambda x: x["mins"]) + [l for l in hs_leads if l["mins"] is None]
    bar_labels = [f"{l['name']}<br><span style='font-size:10px'>{l['company'][:28]}</span>"
                  for l in hs_sorted]
    bar_mins   = [l["mins"] if l["mins"] is not None else 0 for l in hs_sorted]
    bar_text   = [l["label"] for l in hs_sorted]
    bar_colors = []
    for l in hs_sorted:
        if l["mins"] is None:
            bar_colors.append(MUTED)
        elif l["mins"] <= 10:
            bar_colors.append(GREEN)
        elif l["mins"] <= 60:
            bar_colors.append(AMBER)
        else:
            bar_colors.append(RED)

    fig_hs_bar = go.Figure()
    fig_hs_bar.add_trace(go.Bar(
        y=bar_labels,
        x=bar_mins,
        orientation="h",
        marker_color=bar_colors,
        text=bar_text,
        textposition="outside",
        customdata=[[l["source"]] for l in hs_sorted],
        hovertemplate="<b>%{y}</b><br>Response: %{text}<br>Source: %{customdata[0]}<extra></extra>",
    ))
    # Benchmark lines
    fig_hs_bar.add_vline(x=5,   line_dash="dot", line_color=GREEN,
                         annotation_text="5 min target",
                         annotation_position="top right",
                         annotation_font=dict(color=GREEN, size=10))
    fig_hs_bar.add_vline(x=10,  line_dash="dot", line_color=AMBER,
                         annotation_text="10 min threshold",
                         annotation_position="top right",
                         annotation_font=dict(color=AMBER, size=10))
    fig_hs_bar.update_layout(
        title=dict(
            text=f"Lead Response Time — Paid Ad Leads This Quarter  "
                 f"({ct_10min}/{hs_total} contacted within 10 min)",
            font=dict(size=14, color=INK)
        ),
        xaxis=dict(title="Minutes", showgrid=True, gridcolor=RULE,
                   type="log", range=[0, 5]),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font=dict(family="Calibri, Arial", color=BODY),
        showlegend=False,
        margin=dict(t=60, b=40, l=200, r=120),
        height=340,
    )

    # Chart 7 — Lead detail table
    def rt_color(mins):
        """Return solid hex color based on response time."""
        if mins is None: return MUTED
        if mins <= 10:   return GREEN
        if mins <= 60:   return AMBER
        return RED

    def rt_bg(mins):
        """Return light rgba background for response time cell."""
        if mins is None: return "rgba(107,114,128,0.12)"
        if mins <= 10:   return "rgba(109,163,74,0.15)"
        if mins <= 60:   return "rgba(224,162,82,0.15)"
        return "rgba(224,82,82,0.15)"

    tbl_leads = sorted(hs_leads, key=lambda x: (x["mins"] is None, x["mins"] or 9999))
    fig_hs_tbl = go.Figure(data=[go.Table(
        columnwidth=[2, 2.5, 1.5, 1.2, 1.2],
        header=dict(
            values=["Name", "Company", "Source", "Stage", "Response Time"],
            fill_color=INK,
            font=dict(color=WHITE, size=12, family="Calibri, Arial"),
            align="left",
            height=30,
        ),
        cells=dict(
            values=[
                [l["name"]    for l in tbl_leads],
                [l["company"] for l in tbl_leads],
                [l["source"][:30] if l["source"] else "—" for l in tbl_leads],
                [l["stage"]   for l in tbl_leads],
                [l["label"]   for l in tbl_leads],
            ],
            fill_color=[
                [CANVAS if i % 2 == 0 else WHITE for i in range(len(tbl_leads))],
                [CANVAS if i % 2 == 0 else WHITE for i in range(len(tbl_leads))],
                [CANVAS if i % 2 == 0 else WHITE for i in range(len(tbl_leads))],
                [CANVAS if i % 2 == 0 else WHITE for i in range(len(tbl_leads))],
                [rt_bg(l["mins"]) for l in tbl_leads],
            ],
            font=dict(color=[
                [BODY]*len(tbl_leads),
                [BODY]*len(tbl_leads),
                [BODY]*len(tbl_leads),
                [BODY]*len(tbl_leads),
                [rt_color(l["mins"]) for l in tbl_leads],
            ], size=11, family="Calibri, Arial"),
            align="left",
            height=26,
        ),
    )])
    fig_hs_tbl.update_layout(
        title=dict(text="Lead Detail — Paid Ad Leads (Sorted: Fastest to Slowest Response)",
                   font=dict(size=14, color=INK)),
        paper_bgcolor=WHITE,
        margin=dict(t=50, b=10, l=10, r=10),
        height=360,
    )

# ── Load LinkedIn data ─────────────────────────────────────────────────────────
li_daily  = []   # [{date, impr, clicks, reactions, eng_rate}]
li_posts  = []   # [{title, date, impr, clicks, ctr, likes, comments, reposts, eng}]

try:
    import xlrd as _xlrd
    _wb = _xlrd.open_workbook(F_LINKEDIN)

    # Metrics sheet — daily aggregates (row 1 = header, rows 2+ = data)
    _ws = _wb.sheet_by_name("Metrics")
    for _r in range(2, _ws.nrows):
        _row = [_ws.cell_value(_r, _c) for _c in range(_ws.ncols)]
        if not _row[0]:
            continue
        li_daily.append({
            "date":      str(_row[0]),
            "impr":      float(_row[3] or 0),    # total impressions
            "clicks":    float(_row[7] or 0),    # total clicks
            "reactions": float(_row[10] or 0),   # total reactions
            "eng":       float(_row[19] or 0),   # engagement rate total
        })

    # All posts sheet (row 1 = header, rows 2+ = posts)
    _ws2 = _wb.sheet_by_name("All posts")
    for _r in range(2, _ws2.nrows):
        _row = [_ws2.cell_value(_r, _c) for _c in range(_ws2.ncols)]
        if not _row[0]:
            continue
        _title = str(_row[0]).replace("\n", " ").strip()
        li_posts.append({
            "title":    _title[:48] + "…" if len(_title) > 48 else _title,
            "date":     str(_row[5]),
            "impr":     float(_row[9] or 0),
            "clicks":   float(_row[12] or 0),
            "ctr":      float(_row[13] or 0) * 100,
            "likes":    float(_row[14] or 0),
            "comments": float(_row[15] or 0),
            "reposts":  float(_row[16] or 0),
            "eng":      float(_row[18] or 0) * 100,
        })
except Exception:
    pass

li_total_impr   = sum(d["impr"]   for d in li_daily)
li_total_clicks = sum(d["clicks"] for d in li_daily)
li_avg_eng      = sum(d["eng"] for d in li_daily if d["eng"] > 0) / max(1, sum(1 for d in li_daily if d["eng"] > 0))
li_best_post    = max(li_posts, key=lambda x: x["eng"]) if li_posts else None

# Chart — LinkedIn daily trend (impressions + engagement rate)
if li_daily:
    fig_li_trend = go.Figure()
    fig_li_trend.add_trace(go.Bar(
        x=[d["date"] for d in li_daily],
        y=[d["impr"] for d in li_daily],
        name="Impressions",
        marker_color="rgba(109,163,74,0.35)",
        hovertemplate="<b>%{x}</b><br>Impressions: %{y:.0f}<extra></extra>",
    ))
    fig_li_trend.add_trace(go.Scatter(
        x=[d["date"] for d in li_daily],
        y=[d["eng"] * 100 for d in li_daily],
        name="Engagement %",
        mode="lines+markers",
        line=dict(color=DARK_GREEN, width=2),
        marker=dict(size=4),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Engagement: %{y:.1f}%<extra></extra>",
    ))
    fig_li_trend.update_layout(
        title=dict(text="Daily Impressions & Engagement Rate", font=dict(size=15, color=INK)),
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font=dict(family="Calibri, Arial", color=BODY),
        xaxis=dict(showgrid=False, tickangle=-30, nticks=15),
        yaxis=dict(title="Impressions", showgrid=True, gridcolor=RULE),
        yaxis2=dict(title="Engagement %", overlaying="y", side="right",
                    showgrid=False, tickformat=".0f", ticksuffix="%"),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=50, b=60, l=50, r=60),
        height=320,
        barmode="overlay",
    )

# Chart — Post performance (sorted by engagement rate)
if li_posts:
    _ps = sorted(li_posts, key=lambda x: x["eng"])
    fig_li_posts = go.Figure()
    fig_li_posts.add_trace(go.Bar(
        y=[p["title"] for p in _ps],
        x=[p["impr"]  for p in _ps],
        orientation="h",
        name="Impressions",
        marker_color=GREEN,
        text=[f"{p['impr']:.0f}" for p in _ps],
        textposition="outside",
    ))
    fig_li_posts.add_trace(go.Scatter(
        y=[p["title"] for p in _ps],
        x=[p["clicks"] * 3 for p in _ps],   # scale clicks for visibility on same axis
        mode="markers",
        marker=dict(size=10, color=DARK_GREEN, symbol="diamond"),
        name="Clicks (×3 scaled)",
        hovertemplate="<b>%{y}</b><br>Clicks: %{customdata}<extra></extra>",
        customdata=[p["clicks"] for p in _ps],
    ))
    fig_li_posts.update_layout(
        title=dict(
            text=f"Post Performance — sorted by engagement rate  |  Best: {li_best_post['eng']:.1f}% eng on \"{li_best_post['title'][:35]}…\"" if li_best_post else "Post Performance",
            font=dict(size=13, color=INK)
        ),
        xaxis=dict(title="Impressions", showgrid=True, gridcolor=RULE),
        yaxis=dict(showgrid=False),
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font=dict(family="Calibri, Arial", color=BODY, size=10),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=60, b=60, l=280, r=80),
        height=320,
    )

# ── Render all charts ──────────────────────────────────────────────────────────
div_camp   = chart_div(fig_camp)
div_daily  = chart_div(fig_daily)
div_hourly = chart_div(fig_hourly)
div_ag     = chart_div(fig_ag)
div_kw     = chart_div(kw_fig)
div_hs_bar    = chart_div(fig_hs_bar) if hs_leads else ""
div_hs_tbl    = chart_div(fig_hs_tbl) if hs_leads else ""
div_li_trend  = chart_div(fig_li_trend) if li_daily else ""
div_li_posts  = chart_div(fig_li_posts) if li_posts else ""

# ── HTML assembly ──────────────────────────────────────────────────────────────
today      = datetime.today().strftime("%B %d, %Y")
date_range = "March 9 – April 7, 2026"

# KPI card helper
def kpi_card(label, value, sub="", color=GREEN):
    return f"""
<div class="kpi-card">
  <div class="kpi-value" style="color:{color};">{value}</div>
  <div class="kpi-label">{label}</div>
  {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
</div>"""

# Insight alert helper
def alert(icon, text, color=AMBER):
    return f"""
<div class="alert" style="border-left-color:{color};">
  <span class="alert-icon">{icon}</span>
  <span>{text}</span>
</div>"""

# Placeholder card for coming-soon sections
def placeholder_card(title, lines):
    items = "".join(f'<li>{ln}</li>' for ln in lines)
    return f"""
<div class="placeholder-card">
  <div class="ph-title">{title}</div>
  <ul class="ph-list">{items}</ul>
  <div class="ph-badge">Coming next session</div>
</div>"""

kpi_row = (
    kpi_card("Total Spend", f"${total_spend:,.2f}", f"Budget: ~$3,000/mo")
  + kpi_card("Total Clicks", f"{int(total_clicks):,}", f"{date_range}")
  + kpi_card("Conversions", f"{int(total_conv)}", "Form submissions")
  + kpi_card("Avg. CPC", f"${avg_cpc:.2f}", "Cost per click")
  + kpi_card("Cost / Conv.", f"${avg_cpl:,.2f}", "Cost per lead")
)

alerts_html = (
    alert("⚠️", f"<strong>{off_pct:.0f}% of spend (${off_cost:,.0f}) ran outside business hours</strong> (9 AM–5 PM EST target). "
          f"That's {int(off_click)} clicks the team could not follow up on in under 5 minutes.", RED)
  + alert("⚠️", f"<strong>${zero_waste:,.0f} spent on {len(zero_kws)} keywords with zero conversions.</strong> "
          f"Consider pausing these and reallocating to performing terms.", AMBER)
  + alert("✅", f"<strong>Branded campaign is performing well.</strong> CTR: {campaigns[1]['ctr']:.1f}% vs {campaigns[0]['ctr']:.1f}% on RON. "
          f"Branded CPL is ${campaigns[1]['cpl']:,.0f} vs ${campaigns[0]['cpl']:,.0f} on RON.", GREEN)
) if len(campaigns) > 1 else ""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>SIGNiX Marketing Dashboard — {today}</title>
  <script src="https://cdn.plot.ly/plotly-3.4.0.min.js" charset="utf-8"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: Calibri, Arial, sans-serif;
      background: {CANVAS};
      color: {BODY};
      font-size: 14px;
    }}
    /* Header */
    .header {{
      background: {INK};
      color: {WHITE};
      padding: 22px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .header h1 {{ font-size: 22px; font-weight: 700; }}
    .header h1 span {{ color: {GREEN}; }}
    .header-meta {{ font-size: 12px; color: {MUTED}; text-align: right; line-height: 1.6; }}
    /* Section wrappers */
    .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 24px 40px; }}
    .section-title {{
      font-size: 13px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.07em; color: {MUTED}; margin: 28px 0 12px;
      padding-bottom: 6px; border-bottom: 1px solid {RULE};
    }}
    /* KPI row */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
      margin-bottom: 8px;
    }}
    .kpi-card {{
      background: {WHITE};
      border: 1px solid {RULE};
      border-radius: 8px;
      padding: 18px 18px 14px;
    }}
    .kpi-value {{ font-size: 26px; font-weight: 700; line-height: 1.1; }}
    .kpi-label {{ font-size: 12px; color: {MUTED}; margin-top: 5px; font-weight: 600; text-transform: uppercase; }}
    .kpi-sub   {{ font-size: 11px; color: {MUTED}; margin-top: 3px; }}
    /* Two-column row */
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .chart-card {{
      background: {WHITE};
      border: 1px solid {RULE};
      border-radius: 8px;
      padding: 4px 4px 0;
      overflow: hidden;
    }}
    .full-card {{
      background: {WHITE};
      border: 1px solid {RULE};
      border-radius: 8px;
      padding: 4px 4px 0;
      overflow: hidden;
    }}
    /* Alerts */
    .alerts {{ display: flex; flex-direction: column; gap: 10px; margin: 18px 0 8px; }}
    .alert {{
      background: {WHITE};
      border-left: 4px solid {AMBER};
      border-radius: 4px;
      padding: 12px 16px;
      font-size: 13px;
      line-height: 1.5;
      display: flex;
      gap: 10px;
      align-items: flex-start;
    }}
    .alert-icon {{ font-size: 16px; flex-shrink: 0; }}
    /* Placeholder cards */
    .placeholder-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 8px; }}
    .placeholder-card {{
      background: {WHITE};
      border: 1px solid {RULE};
      border-radius: 8px;
      padding: 24px;
      opacity: 0.65;
    }}
    .ph-title  {{ font-size: 16px; font-weight: 700; color: {INK}; margin-bottom: 12px; }}
    .ph-list   {{ padding-left: 18px; color: {MUTED}; font-size: 13px; line-height: 2; }}
    .ph-badge  {{
      display: inline-block; margin-top: 14px;
      background: {CANVAS}; border: 1px solid {RULE};
      border-radius: 20px; padding: 3px 12px;
      font-size: 11px; color: {MUTED}; font-weight: 600; text-transform: uppercase;
    }}
    /* Footer */
    .footer {{
      text-align: center; padding: 20px;
      font-size: 11px; color: {MUTED};
      border-top: 1px solid {RULE};
      margin-top: 32px;
    }}
    @media (max-width: 900px) {{
      .kpi-row, .two-col, .placeholder-row {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 600px) {{
      .kpi-row, .two-col, .placeholder-row {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <h1><span>SIGNiX</span> Marketing Dashboard</h1>
    <div style="font-size:13px; color:{MUTED}; margin-top:4px;">Google Ads &nbsp;·&nbsp; HubSpot Lead Response &nbsp;·&nbsp; LinkedIn &nbsp;·&nbsp; {date_range}</div>
  </div>
  <div class="header-meta">
    Prepared by Chris Teague<br>
    Head of Growth and Marketing<br>
    Generated {today}
  </div>
</div>

<div class="container">

  <!-- KPI Scorecard -->
  <div class="section-title">Campaign Scorecard</div>
  <div class="kpi-row">
    {kpi_row}
  </div>

  <!-- Alerts -->
  <div class="section-title">Key Findings</div>
  <div class="alerts">
    {alerts_html}
  </div>

  <!-- Campaign + Daily Trend -->
  <div class="section-title">Campaign Performance</div>
  <div class="two-col">
    <div class="chart-card">{div_camp}</div>
    <div class="chart-card">{div_daily}</div>
  </div>

  <!-- Hourly Analysis -->
  <div class="section-title">Off-Hours Spend Analysis</div>
  <div class="full-card">{div_hourly}</div>

  <!-- Ad Groups + Keywords -->
  <div class="section-title">Ad Groups & Keywords</div>
  <div class="two-col">
    <div class="chart-card">{div_ag}</div>
    <div class="chart-card">{div_kw}</div>
  </div>

  <!-- HubSpot Lead Response Section -->
  {"" if not hs_leads else f"""
  <div class="section-title">Lead Response Time — HubSpot (Paid Ads · This Quarter)</div>
  <div class="kpi-row" style="grid-template-columns: repeat(4, 1fr);">
    {kpi_card("Avg. Response Time", fmt_duration(avg_resp_mins), f"{hs_total} paid leads total",
              RED if avg_resp_mins > 60 else AMBER)}
    {kpi_card("Within 5 Minutes", f"{ct_5min} / {hs_total}",
              f"{ct_5min/hs_total*100:.0f}% — CEO target",
              GREEN if ct_5min/hs_total >= 0.5 else RED)}
    {kpi_card("Within 10 Minutes", f"{ct_10min} / {hs_total}",
              f"{ct_10min/hs_total*100:.0f}% of leads",
              GREEN if ct_10min/hs_total >= 0.5 else AMBER)}
    {kpi_card("Need Follow-Up", f"{len(hs_no_followup)}",
              "No response or &gt;24 hrs",
              RED if hs_no_followup else GREEN)}
  </div>
  <div class="two-col" style="margin-top:14px;">
    <div class="chart-card">{div_hs_bar}</div>
    <div class="chart-card">{div_hs_tbl}</div>
  </div>
  """}

  <!-- LinkedIn Section -->
  {"" if not li_daily else f"""
  <div class="section-title">LinkedIn Engagement — March 10 – April 8, 2026</div>
  <div class="kpi-row" style="grid-template-columns: repeat(4, 1fr);">
    {kpi_card("Total Impressions", f"{int(li_total_impr):,}", "Organic only")}
    {kpi_card("Total Clicks", f"{int(li_total_clicks):,}", "All posts")}
    {kpi_card("Avg Engagement", f"{li_avg_eng*100:.1f}%", "Days with activity", DARK_GREEN)}
    {kpi_card("Best Post Eng.", f"{li_best_post['eng']:.1f}%" if li_best_post else "—",
              li_best_post['date'] if li_best_post else "", GREEN)}
  </div>
  <div class="two-col" style="margin-top:14px;">
    <div class="chart-card">{div_li_trend}</div>
    <div class="chart-card">{div_li_posts}</div>
  </div>
  """}


</div>

<div class="footer">
  SIGNiX Confidential &nbsp;·&nbsp; Head of Growth and Marketing &nbsp;·&nbsp; signix.com
  &nbsp;·&nbsp; Re-run <code>build_signix_dashboard.py</code> with fresh CSV exports to refresh.
</div>

</body>
</html>"""

# ── Save ───────────────────────────────────────────────────────────────────────
OUT     = "PROJECT-DOCS/SIGNiX_Dashboard_April2026.html"
DESKTOP = os.path.expanduser("~/Desktop/SIGNiX_Dashboard_April2026.html")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"Saved:           {OUT}")

shutil.copy2(OUT, DESKTOP)
print(f"Copied to desktop: {DESKTOP}")
print()
print("── Summary ──────────────────────────────────────────────────────")
print(f"  Total spend:       ${total_spend:,.2f}")
print(f"  Total clicks:      {int(total_clicks):,}")
print(f"  Total conversions: {int(total_conv)}")
print(f"  Avg CPC:           ${avg_cpc:.2f}")
print(f"  Cost per lead:     ${avg_cpl:,.2f}")
print(f"  Off-hours spend:   ${off_cost:,.2f}  ({off_pct:.1f}% of total)")
print(f"  Zero-conv waste:   ${zero_waste:,.2f}  ({len(zero_kws)} keywords)")
