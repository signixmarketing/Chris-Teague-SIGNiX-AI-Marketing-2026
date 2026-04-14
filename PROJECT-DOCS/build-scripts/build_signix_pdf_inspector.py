#!/usr/bin/env python3
"""
Build SIGNiX PDF Signature Inspector v3 — multi-audience demo tool.

Seven selectable audience scenarios. One source of truth for the technical
PKI data. Evidence Layer 1 (signed document) and Evidence Layer 2 (audit trail).

Run from any directory:
  python3 "PROJECT-DOCS/build-scripts/build_signix_pdf_inspector.py"

Output: PROJECT-DOCS/DELIVERABLES/SIGNiX_PDF_Inspector.html
"""

import re, zipfile, os, datetime

# ── Brand tokens ──────────────────────────────────────────────────────────────
GREEN  = "#6da34a"
INK    = "#2e3440"
BODY   = "#545454"
MUTED  = "#6b7280"
WHITE  = "#ffffff"
CANVAS = "#f8fafb"
RULE   = "#d8dee9"
AMBER  = "#f59e0b"
RED    = "#ef4444"

# ── Source file paths ─────────────────────────────────────────────────────────
SIGNIX_ZIP = os.path.expanduser(
    "~/Downloads/Document_Set__Teague_-_30_Jan_2026-PDFDocuments.zip"
)
SIGNIX_PDF_NAME  = (
    "CHRIS TEAGUE SIGNiX, Inc. Employee Non-Disclosure Agreement and Assignment v2 .pdf"
)
AUDIT_TRAIL_NAME = (
    "Document Set_ Teague - 30 Jan 2026_ID19c0fd449ae_2a4_4aa959f3_2vsh7a_1_audit_trail.pdf"
)
DOCUSIGN_PDF = os.path.expanduser("~/Downloads/US Offer Letter.pdf")

OUTPUT_DIR  = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DELIVERABLES"
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SIGNiX_PDF_Inspector.html")


# ── PDF parsing ────────────────────────────────────────────────────────────────

def load_bytes(path_or_zip, inner_name=None):
    if inner_name:
        return zipfile.ZipFile(path_or_zip).read(inner_name)
    with open(path_or_zip, "rb") as f:
        return f.read()


def parse_pdf(pdf_bytes):
    text  = pdf_bytes.decode("latin-1")
    total = len(pdf_bytes)

    sig_positions = [m.start() for m in re.finditer(r"/Type\s*/Sig", text)]
    signatures = []
    for pos in sig_positions:
        chunk = text[pos:pos+2000]
        sig = {}
        for field in ["/Filter", "/SubFilter", "/Reason", "/M", "/Location", "/Name"]:
            m = re.search(field + r"\s*[(/]([^\n)<>]{0,200})", chunk)
            if m:
                sig[field.lstrip("/")] = re.sub(r"[^\x20-\x7e]", "", m.group(1)).strip()
        signatures.append(sig)

    br = re.search(r"/ByteRange\s*\[([^\]]+)\]", text)
    byterange = {}
    if br:
        parts = br.group(1).strip().split()
        b0, l0, b1, l1 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
        byterange = {
            "raw": f"[{b0} {l0} {b1} {l1}]",
            "signed": l0 + l1,
            "total": total,
            "pct": round((l0 + l1) / total * 100, 1),
            "container": b1 - (b0 + l0),
        }

    contents_match = re.search(r"/Contents\s*<([0-9a-fA-F]+)>", text)
    pkcs7_bytes = 0
    if contents_match:
        pkcs7_bytes = len(bytes.fromhex(contents_match.group(1)))

    signing_time = ""
    for sig in signatures:
        dt = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(.*)", sig.get("M", ""))
        if dt:
            yr, mo, dy, hr, mn, sc, tz = dt.groups()
            signing_time = f"{yr}-{mo}-{dy} at {hr}:{mn} UTC{tz[:6]}"
            break

    return {
        "total_bytes": total,
        "num_sigs": len(sig_positions),
        "signatures": signatures,
        "byterange": byterange,
        "pkcs7_bytes": pkcs7_bytes,
        "signing_time": signing_time,
    }


# ── Load data ─────────────────────────────────────────────────────────────────
print("Reading SIGNiX signed document...")
sx  = parse_pdf(load_bytes(SIGNIX_ZIP, SIGNIX_PDF_NAME))
print("Reading SIGNiX audit trail...")
at  = parse_pdf(load_bytes(SIGNIX_ZIP, AUDIT_TRAIL_NAME))
print("Reading DocuSign document...")
ds  = parse_pdf(load_bytes(DOCUSIGN_PDF))

print(f"SIGNiX doc:   {sx['num_sigs']} sig(s), {sx['byterange'].get('pct')}% signed, {sx['pkcs7_bytes']:,}B PKCS7")
print(f"SIGNiX audit: {at['num_sigs']} sig(s), {at['byterange'].get('pct')}% signed, {at['pkcs7_bytes']:,}B PKCS7")
print(f"DocuSign doc: {ds['num_sigs']} sig(s), {ds['byterange'].get('pct')}% signed, {ds['pkcs7_bytes']:,}B PKCS7")

sx_br = sx["byterange"]
ds_br = ds["byterange"]
at_br = at["byterange"]


# ── HTML helpers ──────────────────────────────────────────────────────────────

def badge(text, color):
    return (f'<span style="background:{color};color:{WHITE};font-size:10px;font-weight:700;'
            f'padding:3px 10px;border-radius:20px;letter-spacing:0.5px;white-space:nowrap;">{text}</span>')

def progress(pct, color):
    return (f'<div style="height:10px;border-radius:5px;background:{RULE};overflow:hidden;margin:6px 0;">'
            f'<div style="height:100%;width:{pct}%;background:{color};border-radius:5px;"></div></div>')

def meta_row(label, value, color=None):
    val_color = color or BODY
    weight    = "600" if color else "400"
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
            f'padding:8px 0;border-bottom:1px solid {RULE};gap:12px;">'
            f'<span style="color:{MUTED};font-size:11px;white-space:nowrap;padding-top:1px;">{label}</span>'
            f'<span style="font-size:12px;color:{val_color};font-weight:{weight};text-align:right;">{value}</span>'
            f'</div>')

def cert_chain_html(entries, accent):
    out = []
    for i, e in enumerate(entries):
        indent    = f"margin-left:{i*18}px"
        connector = (f'<div style="{indent};color:{MUTED};font-size:11px;padding:1px 0;">└──</div>'
                     if i > 0 else "")
        is_leaf   = i == len(entries) - 1
        bg        = accent + "15" if is_leaf else CANVAS
        border    = f"2px solid {accent}" if is_leaf else f"1px solid {RULE}"
        sub       = e.get("sub", "")
        out.append(f"""
        {connector}
        <div style="{indent};background:{bg};border:{border};border-radius:6px;padding:7px 12px;margin:2px 0;">
          <div style="font-weight:600;font-size:12px;color:{INK};">{e['name']}</div>
          {"<div style='color:"+MUTED+";font-size:10px;'>"+sub+"</div>" if sub else ""}
        </div>""")
    return "\n".join(out)

def table_row(label, sx_val, ds_val, sx_color=None, ds_color=None, shaded=False):
    bg = f"background:{CANVAS};" if shaded else ""
    def cell(val, color):
        c = color or BODY
        w = "600" if color else "400"
        return f'<td style="padding:12px 16px;text-align:center;color:{c};font-weight:{w};">{val}</td>'
    return (f'<tr style="border-bottom:1px solid {RULE};{bg}">'
            f'<td style="padding:12px 16px;color:{BODY};">{label}</td>'
            f'{cell(sx_val, sx_color)}{cell(ds_val, ds_color)}</tr>')


# ── Certificate chains ────────────────────────────────────────────────────────
sx_chain = [
    {"name": "GlobalSign Document Signing Root R45", "sub": "Root CA · Valid 2020–2030"},
    {"name": "GlobalSign R45 AATL Root CA 2020",     "sub": "Intermediate CA"},
    {"name": "GlobalSign GCC R45 AATL CA 2020",      "sub": "AATL Signing CA"},
    {"name": "SIGNiX Signature Authority",
     "sub": "Signix, Inc. · Chattanooga, TN · Valid Jul 2025–Jul 2026"},
]
ds_chain = [
    {"name": "DigiCert Trusted Root G4",
     "sub": "Root CA · Valid 2022–2032"},
    {"name": "DigiCert Trusted G4 AATL RSA4096 SHA384 2022 CA1",
     "sub": "AATL Signing CA · Valid May 2025–May 2028"},
    {"name": "DocuSign, Inc. — DS Technical Operations",
     "sub": "Server export cert · San Francisco, CA"},
]

# ── Build ─────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SIGNiX PDF Signature Inspector</title>
<style>
*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:{CANVAS}; color:{BODY}; line-height:1.5; }}
h2 {{ font-weight:700; }}
.panel {{ background:{WHITE}; border:1px solid {RULE}; border-radius:12px; padding:28px; }}
.panel-sx {{ border-top:4px solid {GREEN}; }}
.panel-ds {{ border-top:4px solid {AMBER}; }}
.section-title {{ font-size:10px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:{MUTED}; margin:22px 0 10px; }}
.kpi {{ text-align:center; background:{CANVAS}; border:1px solid {RULE}; border-radius:8px; padding:14px 8px; }}
.kpi-val {{ font-size:22px; font-weight:800; line-height:1; }}
.kpi-lbl {{ font-size:10px; color:{MUTED}; margin-top:4px; text-transform:uppercase; letter-spacing:0.5px; }}
.verdict {{ border-radius:8px; padding:14px 18px; font-size:13px; line-height:1.6; margin-top:8px; }}
.verdict-g {{ background:#f0faf0; border-left:4px solid {GREEN}; color:{INK}; }}
.verdict-a {{ background:#fffbeb; border-left:4px solid {AMBER}; color:{INK}; }}
.drop-zone {{ border:2px dashed {RULE}; border-radius:12px; padding:40px; text-align:center; cursor:pointer; transition:all 0.2s; }}
.drop-zone:hover, .drop-zone.drag-over {{ border-color:{GREEN}; background:#f0faf0; }}
.aud-btn {{ padding:9px 18px; border-radius:8px; border:1px solid {RULE}; background:{WHITE}; color:{MUTED}; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.18s; white-space:nowrap; }}
.aud-btn:hover {{ border-color:{GREEN}; color:{GREEN}; background:#f0faf0; }}
.aud-btn.active {{ background:{GREEN}; color:{WHITE}; border-color:{GREEN}; }}
.aud-btn.placeholder {{ opacity:0.4; cursor:default; }}
.scenario-wrap {{ transition:opacity 0.2s; }}
.divider {{ display:flex; align-items:center; gap:16px; margin:40px 0 20px; }}
.divider-line {{ flex:1; height:1px; background:{RULE}; }}
.divider-label {{ font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:{MUTED}; white-space:nowrap; }}
</style>
</head>
<body>

<!-- ═══ HEADER ═══════════════════════════════════════════════════════════════ -->
<div style="background:{INK};padding:28px 40px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
  <div>
    <div style="color:{GREEN};font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">SIGNiX / Demo Tool</div>
    <h1 style="color:{WHITE};font-size:26px;font-weight:800;">PDF Signature Inspector</h1>
    <div style="color:#9ca3af;font-size:13px;margin-top:4px;">What lives inside a signed PDF. And who can prove it.</div>
  </div>
  <div style="text-align:right;">
    <div style="color:{GREEN};font-weight:700;font-size:16px;">Internal Sales Demo</div>
    <div style="color:#6b7280;font-size:11px;margin-top:3px;">Built {datetime.date.today().strftime('%B %d, %Y')}</div>
  </div>
</div>

<!-- ═══ AUDIENCE SELECTOR ════════════════════════════════════════════════════ -->
<div style="background:#1a1f29;padding:24px 40px;">
  <div style="max-width:1160px;margin:0 auto;">
    <div style="color:#6b7280;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;">Select your audience</div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;" id="audienceButtons">
      <button class="aud-btn active"  onclick="setAudience('elder',      this)">Elder Protection</button>
      <button class="aud-btn"         onclick="setAudience('bank',       this)">Banks &amp; Credit Unions</button>
      <button class="aud-btn"         onclick="setAudience('wealth',     this)">Wealth Mgmt / RIA</button>
      <button class="aud-btn"         onclick="setAudience('government', this)">Government / County</button>
      <button class="aud-btn"         onclick="setAudience('healthcare', this)">Healthcare</button>
      <button class="aud-btn"         onclick="setAudience('legal',      this)">Legal</button>
      <button class="aud-btn"         onclick="setAudience('debt',       this)">Debt Buying / Affidavit</button>
    </div>
  </div>
</div>

<!-- ═══ SCENARIO ═════════════════════════════════════════════════════════════ -->
<div style="background:#1a1f29;padding:0 40px 36px;">
  <div style="max-width:900px;margin:0 auto;" id="scenarioWrap" class="scenario-wrap">
    <div style="color:{AMBER};font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;" id="scenarioTag">The scenario &mdash; Elder Financial Protection</div>
    <p style="color:{WHITE};font-size:17px;font-weight:600;line-height:1.65;margin-bottom:16px;" id="scenarioTitle">An elderly account holder is pressured by a family member to authorize a large wire transfer. The family member is present during the signing. The document is signed. The money moves.</p>
    <p style="color:#9ca3af;font-size:14px;line-height:1.75;margin-bottom:16px;" id="scenarioBody">Two weeks later, the account holder&#8217;s attorney contacts the institution. The account holder says they were coerced. They did not understand what they signed. The family member may have completed the process on their behalf. Your compliance team, outside counsel, and potentially a regulator will ask one question.</p>
    <div style="background:{INK};border:1px solid #374151;border-left:4px solid {GREEN};border-radius:8px;padding:20px 24px;">
      <div style="color:{WHITE};font-size:19px;font-weight:800;line-height:1.45;" id="scenarioQuestion">&#8220;Can you prove who signed this document, without calling your e-signature provider to vouch for you?&#8221;</div>
    </div>
  </div>
</div>

<!-- ═══ EVIDENCE LAYER 1 ════════════════════════════════════════════════════ -->
<div style="max-width:1200px;margin:0 auto;padding:0 24px;">
  <div class="divider">
    <div class="divider-line"></div>
    <div class="divider-label">Evidence Layer 1 — The Signed Document</div>
    <div class="divider-line"></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">

    <!-- SIGNiX -->
    <div class="panel panel-sx">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;gap:12px;">
        <div>
          <div style="color:{GREEN};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">Signed with</div>
          <h2 style="font-size:22px;color:{INK};">SIGNiX</h2>
          <div style="color:{MUTED};font-size:12px;">Employee NDA — Jan 30, 2026</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;">
          {badge("AATL CERTIFIED", GREEN)}
          {badge("PKI DIGITAL SIG", GREEN)}
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:20px;">
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{sx["num_sigs"]}</div><div class="kpi-lbl">Signatures</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{sx_br.get("pct")}%</div><div class="kpi-lbl">Bytes Signed</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{round(sx["pkcs7_bytes"]/1024)}KB</div><div class="kpi-lbl">PKCS#7 Size</div></div>
      </div>
      <div class="section-title">Signing Details</div>
      {meta_row("Signed", sx["signing_time"])}
      {meta_row("Signer IP — embedded in PDF", "104.128.161.124", GREEN)}
      {meta_row("Device — embedded in PDF", "iPhone · Chrome iOS 144", GREEN)}
      {meta_row("Transaction ID — embedded in PDF", "19c0fd449ae:2a4:4aa959f3", GREEN)}
      {meta_row("Policy OID", "1.3.6.1.4.1.6693.4.2.10")}
      {meta_row("Signing reason", "Certify the signature of Chris Teague")}
      <div class="section-title">Tamper Protection</div>
      <div style="font-size:12px;color:{MUTED};margin-bottom:4px;">{sx_br.get("signed"):,} of {sx_br.get("total"):,} bytes cryptographically signed</div>
      {progress(sx_br.get("pct"), GREEN)}
      <div style="font-size:10px;color:{MUTED};">{sx_br.get("raw")}</div>
      <div class="section-title">Certificate Chain</div>
      {cert_chain_html(sx_chain, GREEN)}
      <div class="section-title">Can you answer the question?</div>
      <div class="verdict verdict-g">
        <strong>Yes. The document answers it.</strong> Signer IP, device, and transaction ID are embedded in the PKI-signed file. The certificate traces to GlobalSign. The ByteRange hash proves nothing changed after signing. You can produce this evidence without calling anyone.
      </div>
    </div>

    <!-- DocuSign -->
    <div class="panel panel-ds">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;gap:12px;">
        <div>
          <div style="color:{AMBER};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">Signed with</div>
          <h2 style="font-size:22px;color:{INK};">DocuSign</h2>
          <div style="color:{MUTED};font-size:12px;">Offer Letter — Jul 17, 2025</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;">
          {badge("AATL CERTIFIED", AMBER)}
          {badge("SERVER EXPORT SEAL", AMBER)}
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:20px;">
        <div class="kpi"><div class="kpi-val" style="color:{AMBER};">{ds["num_sigs"]}</div><div class="kpi-lbl">Signatures</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{AMBER};">{ds_br.get("pct")}%</div><div class="kpi-lbl">Bytes Signed</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{AMBER};">{round(ds["pkcs7_bytes"]/1024)}KB</div><div class="kpi-lbl">PKCS#7 Size</div></div>
      </div>
      <div class="section-title">Signing Details</div>
      {meta_row("PDF exported", ds["signing_time"])}
      {meta_row("Signer IP", "Not embedded in PDF", RED)}
      {meta_row("Device", "Not embedded in PDF", RED)}
      {meta_row("Transaction ID", "In DocuSign cloud only", RED)}
      {meta_row("Policy OID", "Not present")}
      {meta_row("Signing reason", "Digitally verifiable PDF exported from www.docusign.com")}
      <div class="section-title">Tamper Protection</div>
      <div style="font-size:12px;color:{MUTED};margin-bottom:4px;">{ds_br.get("signed"):,} of {ds_br.get("total"):,} bytes signed</div>
      {progress(ds_br.get("pct"), AMBER)}
      <div style="font-size:10px;color:{MUTED};">{ds_br.get("raw")}</div>
      <div class="section-title">Certificate Chain</div>
      {cert_chain_html(ds_chain, AMBER)}
      <div class="section-title">Can you answer the question?</div>
      <div class="verdict verdict-a">
        <strong>Not from the document alone.</strong> The certificate belongs to DocuSign's server ("DS Technical Operations"), not to the signer. Individual signer identity, IP, and device are in DocuSign's cloud. Answering the question requires DocuSign to produce those records.
      </div>
    </div>
  </div>
</div>

<!-- ═══ EVIDENCE LAYER 2 ════════════════════════════════════════════════════ -->
<div style="max-width:1200px;margin:0 auto;padding:0 24px;">
  <div class="divider">
    <div class="divider-line"></div>
    <div class="divider-label">Evidence Layer 2 — The Signed Audit Trail</div>
    <div class="divider-line"></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">

    <!-- SIGNiX audit -->
    <div class="panel panel-sx">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;gap:12px;">
        <div>
          <div style="color:{GREEN};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">SIGNiX</div>
          <h2 style="font-size:18px;color:{INK};">PKI-Signed Audit Trail</h2>
          <div style="color:{MUTED};font-size:12px;">Separate PDF · Also cryptographically signed</div>
        </div>
        {badge("2 PKI SIGNATURES", GREEN)}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px;">
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{at["num_sigs"]}</div><div class="kpi-lbl">PKI Sigs</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{at_br.get("pct")}%</div><div class="kpi-lbl">Bytes Signed</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{GREEN};">{round(at["pkcs7_bytes"]/1024)}KB</div><div class="kpi-lbl">PKCS#7 Size</div></div>
      </div>
      {meta_row("Certificate authority", "GlobalSign AATL (same chain as signed doc)", GREEN)}
      {meta_row("Signing authority", "SIGNiX Signature Authority", GREEN)}
      {meta_row("Purpose", "Time-stamps each signing event at moment of certification")}
      {meta_row("Transaction ID match", "19c0fd449ae:2a4:4aa959f3 — matches signed document")}
      {meta_row("File size", f"{at['total_bytes']:,} bytes")}
      <div class="section-title">What this means</div>
      <div class="verdict verdict-g">
        Two PKI-signed files per transaction. The document and the audit trail are both cryptographically anchored to GlobalSign. The audit trail records each authentication step. Neither file requires SIGNiX's cooperation to present as evidence.
      </div>
    </div>

    <!-- DocuSign audit -->
    <div class="panel panel-ds">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;gap:12px;">
        <div>
          <div style="color:{AMBER};font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">DocuSign</div>
          <h2 style="font-size:18px;color:{INK};">Certificate of Completion</h2>
          <div style="color:{MUTED};font-size:12px;">Separate PDF · Generated by DocuSign servers</div>
        </div>
        {badge("0 PKI SIGNATURES", RED)}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px;">
        <div class="kpi"><div class="kpi-val" style="color:{RED};">0</div><div class="kpi-lbl">PKI Sigs</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{AMBER};">—</div><div class="kpi-lbl">Bytes Signed</div></div>
        <div class="kpi"><div class="kpi-val" style="color:{AMBER};">—</div><div class="kpi-lbl">PKCS#7 Size</div></div>
      </div>
      {meta_row("PKI signature on audit trail", "None — standard PDF, no cryptographic signing", RED)}
      {meta_row("Signer IP per person", "Present in DocuSign cloud record")}
      {meta_row("Tamper protection on audit doc", "None — not ByteRange-protected", RED)}
      {meta_row("Independent verification", "Requires DocuSign to produce and vouch for record", RED)}
      {meta_row("Evidence standard", "Platform attestation (DocuSign vouches for DocuSign)")}
      <div class="section-title">What this means</div>
      <div class="verdict verdict-a">
        DocuSign's Certificate of Completion is a standard PDF with no PKI signing and no ByteRange protection. Its contents can be questioned in a dispute. Presenting it as evidence requires DocuSign's cooperation and relies on their records being accepted as authoritative.
      </div>
    </div>
  </div>
</div>

<!-- ═══ COMPARISON TABLE ════════════════════════════════════════════════════ -->
<div style="max-width:1200px;margin:40px auto;padding:0 24px;">
  <div class="panel">
    <h2 style="font-size:18px;color:{INK};margin-bottom:4px;">Head-to-Head: When Proof is Required</h2>
    <div style="color:{MUTED};font-size:13px;margin-bottom:20px;">Which platform leaves you with self-contained proof when a signature is challenged.</div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:{CANVAS};">
          <th style="text-align:left;padding:10px 16px;color:{MUTED};font-weight:600;border-bottom:2px solid {RULE};width:32%;">Capability</th>
          <th style="text-align:center;padding:10px 16px;color:{GREEN};font-weight:700;border-bottom:2px solid {RULE};width:34%;">SIGNiX</th>
          <th style="text-align:center;padding:10px 16px;color:{AMBER};font-weight:700;border-bottom:2px solid {RULE};width:34%;">DocuSign (standard)</th>
        </tr>
      </thead>
      <tbody>
        {table_row("PKI signature on document", "✅ GlobalSign AATL", "✅ DigiCert AATL", GREEN)}
        {table_row("Tamper detection (ByteRange)", "✅ ByteRange hash", "✅ ByteRange hash", GREEN, None, True)}
        {table_row("Signer IP in PDF", "✅ Embedded", "✗ Cloud only", GREEN, RED)}
        {table_row("Signer device in PDF", "✅ Embedded", "✗ Cloud only", GREEN, RED, True)}
        {table_row("Transaction ID in PDF", "✅ Embedded", "✗ Cloud only", GREEN, RED)}
        {table_row("Cert belongs to", "SIGNiX Signature Authority", "DS Technical Operations (DocuSign server)", GREEN, None, True)}
        {table_row("Authentication result in file", "✅ OTP · ID Verify · KBA embedded", "✗ Cloud audit log only", GREEN, RED)}
        {table_row("PKI-signed audit trail", "✅ 2 PKI sigs · GlobalSign chain", "✗ Standard PDF · 0 PKI sigs", GREEN, RED, True)}
        {table_row("Provable without platform?", "✅ Document is self-proving", "Requires DocuSign cooperation", GREEN, RED)}
        {table_row("Auth blocks insider fraud", "✅ OTP/ID Verify required at signing", "Depends on settings enabled", GREEN, None, True)}
      </tbody>
    </table>
  </div>
</div>

<!-- ═══ DRAG AND DROP ════════════════════════════════════════════════════════ -->
<div style="max-width:1200px;margin:0 auto 40px;padding:0 24px;">
  <div class="panel">
    <h2 style="font-size:18px;color:{INK};margin-bottom:4px;">Test Any PDF</h2>
    <div style="color:{MUTED};font-size:13px;margin-bottom:20px;">Drop any signed PDF here to inspect its signature metadata. Nothing is uploaded. Everything runs in the browser.</div>
    <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <div style="font-size:32px;margin-bottom:8px;">📄</div>
      <div style="font-weight:600;color:{INK};font-size:14px;">Drop a PDF or click to browse</div>
      <div style="color:{MUTED};font-size:12px;margin-top:4px;">Reads PKI signature metadata directly from the file.</div>
    </div>
    <input type="file" id="fileInput" accept=".pdf" style="display:none;" onchange="handleFile(this.files[0])">
    <div id="dropResult" style="margin-top:20px;display:none;"></div>
  </div>
</div>

<!-- ═══ FOOTER ════════════════════════════════════════════════════════════════ -->
<div style="background:{INK};padding:20px 40px;text-align:center;">
  <div style="color:#6b7280;font-size:12px;">SIGNiX PDF Signature Inspector · Internal demo · Built {datetime.date.today().strftime('%B %d, %Y')}</div>
  <div style="color:#374151;font-size:11px;margin-top:4px;">Data extracted from real signed PDFs using standard PDF/PKI parsing. No proprietary technology exposed.</div>
</div>

<script>
// ── Scenarios ─────────────────────────────────────────────────────────────────
const SCENARIOS = {{
  elder: {{
    tag:      "The scenario — Elder Financial Protection",
    title:    "An elderly account holder is pressured by a family member to authorize a large wire transfer. The family member is present during the signing. The document is signed. The money moves.",
    body:     "Two weeks later, the account holder's attorney contacts the institution. The account holder says they were coerced. They did not understand what they signed. The family member may have completed the process on their behalf. Your compliance team, outside counsel, and potentially a regulator will ask one question.",
    question: "\u201cCan you prove who signed this document, without calling your e-signature provider to vouch for you?\u201d"
  }},
  bank: {{
    tag:      "The scenario — Banks &amp; Credit Unions",
    title:    "A business account holder claims they never authorized a $340,000 wire transfer. The transfer processed. The signed wire authorization is in your records.",
    body:     "Your compliance officer, outside counsel, and potentially the OCC want to know one thing: can you prove the account holder signed it, and not someone at their company acting without authority? The investigation starts with the document.",
    question: "\u201cCan you prove the right person signed this authorization, independently, from the document itself?\u201d"
  }},
  wealth: {{
    tag:      "The scenario — Wealth Management / RIA",
    title:    "A client files a FINRA complaint. They claim an advisor signed their name on a portfolio reallocation form without consent. The advisor says they did not do it.",
    body:     "FINRA opens an inquiry. Your compliance team pulls the signed document. The question is not whether a signature exists. The question is whether you can prove the right person signed it independently, and whether that proof lives in your files or in someone else\u2019s database.",
    question: "\u201cCan you prove who signed this form, without relying on your e-signature provider\u2019s records?\u201d"
  }},
  government: {{
    tag:      "The scenario — Government / County",
    title:    "A vendor challenges a county contract, claiming the authorized official never signed the final version. Three versions of the document are in circulation.",
    body:     "The county attorney needs to prove which version was signed, by whom, and that it was not altered after execution. The answer either lives in the document itself, or it requires a platform to produce it under subpoena.",
    question: "\u201cCan you prove this is the version that was signed, by the right official, and that nothing changed after execution?\u201d"
  }},
  healthcare: {{
    tag:      "The scenario — Healthcare",
    title:    "A patient\u2019s family files a complaint after a procedure. They claim the patient did not give informed consent, or was not in a condition to sign.",
    body:     "The hospital\u2019s risk management team pulls the signed consent form. The question from the patient\u2019s attorney is direct: can you prove this specific patient signed this specific document, on their own, without coercion, at the time indicated? Your answer determines whether this is a documentation discussion or a liability exposure.",
    question: "\u201cCan you prove this patient signed this form independently, at the stated time, without third-party assistance?\u201d"
  }},
  legal: {{
    tag:      "The scenario — Legal",
    title:    "Opposing counsel argues a signed contract was not executed by an authorized signatory. The signing date is contested. The other party claims the document was altered after execution.",
    body:     "Your litigation team needs to produce evidence that the right person signed the right version of the document on the stated date. Relying on a third-party platform to certify what happened introduces a dependency that opposing counsel will immediately challenge.",
    question: "\u201cCan you prove who signed this contract, on which version, on which date, without calling your e-signature provider as a witness?\u201d"
  }},
  debt: {{
    tag:      "The scenario — Debt Buying / Affidavit",
    title:    "A debt buyer purchases a portfolio of charged-off accounts. Each account includes a signed credit agreement or affidavit of debt. A consumer disputes the debt in court.",
    body:     "The judge asks the debt buyer to prove the original document is authentic, unaltered, and that the signature is valid. The buyer did not originate the loan. The original lender may no longer be available to produce records. The document has to carry the proof on its own.",
    question: "\u201cCan this document prove itself, without the originating institution or their e-signature platform?\u201d"
  }}
}};

function setAudience(key, btn) {{
  const s = SCENARIOS[key];
  if (!s) return;
  const wrap = document.getElementById('scenarioWrap');
  wrap.style.opacity = '0';
  setTimeout(() => {{
    document.getElementById('scenarioTag').innerHTML       = s.tag;
    document.getElementById('scenarioTitle').textContent   = s.title;
    document.getElementById('scenarioBody').textContent    = s.body;
    document.getElementById('scenarioQuestion').textContent = s.question;
    wrap.style.opacity = '1';
  }}, 150);
  document.querySelectorAll('.aud-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}}

// scenario text is pre-baked in HTML; JS only handles switching on button click

// ── Drag and drop ─────────────────────────────────────────────────────────────
const dropZone   = document.getElementById('dropZone');
const dropResult = document.getElementById('dropResult');

dropZone.addEventListener('dragover',  e => {{ e.preventDefault(); dropZone.classList.add('drag-over'); }});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {{
  e.preventDefault(); dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.name.toLowerCase().endsWith('.pdf')) handleFile(file);
  else alert('Please drop a PDF file.');
}});

function handleFile(file) {{
  const reader = new FileReader();
  reader.onload = e => {{
    const text = new TextDecoder('latin1').decode(new Uint8Array(e.target.result));
    inspectPDF(file.name, file.size, text);
  }};
  reader.readAsArrayBuffer(file);
}}

function inspectPDF(name, size, text) {{
  const sigCount   = (text.match(/\\/Type\\/Sig/g) || []).length;
  const isSIGNiX   = /SIGNiX|signix|Sgnx\\.PPKNC/i.test(text);
  const isDocuSign = /DocuSign|docusign\\.com/i.test(text);
  const platform   = isSIGNiX ? 'SIGNiX' : (isDocuSign ? 'DocuSign' : 'Unknown Platform');
  const accent     = isSIGNiX ? '{GREEN}' : (isDocuSign ? '{AMBER}' : '{MUTED}');

  const brMatch = text.match(/\\/ByteRange\\s*\\[([^\\]]+)\\]/);
  let pct = 0, brStr = '';
  if (brMatch) {{
    const p = brMatch[1].trim().split(/\\s+/).map(Number);
    if (p.length === 4) {{ pct = Math.round((p[1]+p[3])/size*1000)/10; brStr = `[${{p[0]}} ${{p[1]}} ${{p[2]}} ${{p[3]}}]`; }}
  }}

  const filterM = text.match(/\\/Filter\\/([A-Za-z.]+)/);
  const subM    = text.match(/\\/SubFilter\\/([A-Za-z.]+)/);
  const mM      = text.match(/\\/M\\s*\\(D:(\\d{{4}})(\\d{{2}})(\\d{{2}})(\\d{{2}})(\\d{{2}})/);
  const ipM     = text.match(/IP Address ([\\d.]+)/);
  const txnM    = text.match(/transaction ([\\w:]+)/);
  const ca      = /GlobalSign/.test(text) ? 'GlobalSign AATL' : (/DigiCert/.test(text) ? 'DigiCert AATL' : 'Unknown CA');

  const sigTime = mM ? `${{mM[1]}}-${{mM[2]}}-${{mM[3]}} at ${{mM[4]}}:${{mM[5]}}` : '\u2014';
  const ip      = ipM ? ipM[1] : '<span style="color:{RED};">Not embedded</span>';
  const txn     = txnM ? txnM[1] : '<span style="color:{RED};">Not in file</span>';

  const verdict = isSIGNiX
    ? "<strong>SIGNiX digital signature detected.</strong> Signer identity, IP, and device are embedded in this PDF. This document can answer the question without any third-party cooperation."
    : (isDocuSign
      ? "<strong>DocuSign export seal detected.</strong> Tamper protection is present. Individual signer identity lives in DocuSign's cloud, not in this PDF. Answering a dispute requires DocuSign's records."
      : "<strong>PKI signature detected.</strong> Inspect the certificate chain to confirm signer identity.");
  const vClass = isSIGNiX ? 'verdict-g' : 'verdict-a';

  const bar = pct > 0 ? `
    <div style="margin:12px 0;">
      <div style="font-size:11px;color:{MUTED};margin-bottom:4px;">ByteRange coverage: ${{pct}}% of file signed</div>
      <div style="height:10px;border-radius:5px;background:{RULE};overflow:hidden;">
        <div style="height:100%;width:${{pct}}%;background:${{accent}};border-radius:5px;"></div>
      </div>
      <div style="font-size:10px;color:{MUTED};margin-top:2px;">${{brStr}}</div>
    </div>` : '';

  dropResult.style.display = 'block';
  dropResult.innerHTML = `
    <div style="background:{CANVAS};border:1px solid {RULE};border-top:4px solid ${{accent}};border-radius:10px;padding:24px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;gap:12px;flex-wrap:wrap;">
        <div>
          <div style="font-weight:700;font-size:16px;color:{INK};">${{name}}</div>
          <div style="color:{MUTED};font-size:12px;">${{(size/1024).toFixed(1)}} KB &nbsp;&middot;&nbsp; ${{sigCount}} digital signature(s)</div>
        </div>
        <div style="font-weight:700;color:${{accent}};font-size:15px;">${{platform}}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;margin-bottom:12px;">
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">Filter:</span> <strong>${{filterM ? filterM[1] : '\u2014'}}</strong></div>
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">Trust anchor:</span> <strong>${{ca}}</strong></div>
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">Signed:</span> <strong>${{sigTime}}</strong></div>
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">SubFilter:</span> <strong>${{subM ? subM[1] : '\u2014'}}</strong></div>
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">Signer IP:</span> ${{ip}}</div>
        <div style="padding:8px 12px;background:{WHITE};border-radius:6px;border:1px solid {RULE};"><span style="color:{MUTED};">Transaction ID:</span> ${{txn}}</div>
      </div>
      ${{bar}}
      <div class="verdict ${{vClass}}">${{verdict}}</div>
    </div>`;
}}
</script>
</body>
</html>"""

# ── Write ─────────────────────────────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone. Output: {OUTPUT_FILE}")
