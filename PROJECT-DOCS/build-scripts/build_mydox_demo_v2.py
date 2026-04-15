#!/usr/bin/env python3
"""
Build SIGNiX MyDox Interactive Demo v2

New in v2 vs v1:
  - Screen  5: Signature Tagging (sender wizard — Signatures tab, HTML-rendered)
  - Screens 10-18: Full ID Verify / Persona sub-screens (HTML-rendered, Full Flow only)
  - Screen 19: SIGNiX — ID documents passed
  - Screen 20: SIGNiX — Let's Create Your Signature
  - Screen 23: Confirmation includes QR code for Aspen's calendar + contact info
  - Control bar: Quick View / Full Flow toggle
  - Quick View (default): 14 screens
  - Full Flow:            23 screens — shows every Persona step

Run:
  python3 "PROJECT-DOCS/build-scripts/build_mydox_demo_v2.py"

Output:
  PROJECT-DOCS/DELIVERABLES/SIGNiX_MyDox_Demo.html
"""

import os, base64, subprocess
from io import BytesIO

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "DELIVERABLES")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Contact — update here if Aspen is reassigned ──────────────────────────────
ASPEN_CALENDAR = "https://www.signix.com/meetings/aarias5?uuid=83e31d03-9c7e-41ec-b8a0-feb138363f27"
ASPEN_PHONE    = "(423) 635-7112"
ASPEN_EMAIL    = "aarias@signix.com"

# ── QR Code ────────────────────────────────────────────────────────────────────
qr_b64 = None
try:
    import qrcode
    qr = qrcode.QRCode(version=2, box_size=6, border=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(ASPEN_CALENDAR)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#2e3440", back_color="white")
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    print("QR code: generated OK")
except Exception as exc:
    print(f"QR code: skipped ({exc}) — using text fallback")

if qr_b64:
    QR_BLOCK = f'''<div class="confirm-qr-block">
        <div class="confirm-qr-label">Book a Meeting</div>
        <img src="data:image/png;base64,{qr_b64}" style="width:130px;height:130px;display:block;margin:0 auto;border-radius:6px;" alt="Aspen Calendar" />
        <div class="confirm-qr-contact"><strong>Aspen Arias</strong><br>Account Executive<br>{ASPEN_PHONE}<br>{ASPEN_EMAIL}</div>
      </div>'''
else:
    QR_BLOCK = f'''<div class="confirm-qr-block">
        <div class="confirm-qr-label">Connect with Aspen</div>
        <div style="width:130px;height:130px;display:flex;align-items:center;justify-content:center;background:var(--canvas);border:1px solid var(--rule);border-radius:6px;margin:0 auto;font-size:11px;color:var(--muted);text-align:center;padding:8px;">
          signix.com/<br>meetings/<br>aarias5</div>
        <div class="confirm-qr-contact"><strong>Aspen Arias</strong><br>Account Executive<br>{ASPEN_PHONE}<br>{ASPEN_EMAIL}</div>
      </div>'''

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --green:#6da34a; --green2:#5a8c3b; --ink:#2e3440; --body:#545454;
    --muted:#6b7280; --white:#ffffff; --canvas:#f8fafb; --rule:#d8dee9;
    --yellow:#fffbcc; --red:#c0392b; --blue:#2980b9;
    --persona:#1a56db; --persona2:#1e40af;
  }
  html,body { height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; background:#e8edf2; color:var(--body); font-size:14px; }
  .demo-shell { max-width:1024px; margin:0 auto; background:var(--white); min-height:100vh; display:flex; flex-direction:column; box-shadow:0 0 40px rgba(0,0,0,0.15); }

  /* Control bar */
  .ctrl-bar { background:var(--ink); padding:8px 16px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .ctrl-bar .demo-label { font-size:11px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--green); }
  .ctrl-bar .step-counter { font-size:12px; color:rgba(255,255,255,.6); }
  .ctrl-bar .btn-reset { font-size:11px; font-weight:700; padding:4px 12px; background:transparent; border:1px solid rgba(255,255,255,.3); color:rgba(255,255,255,.7); border-radius:4px; cursor:pointer; }
  .ctrl-bar .btn-reset:hover { border-color:var(--green); color:var(--green); }
  .ctrl-bar .btn-notes { font-size:11px; font-weight:700; padding:4px 10px; background:var(--green); border:none; color:var(--white); border-radius:4px; cursor:pointer; }
  .ctrl-bar .btn-flow { font-size:11px; font-weight:700; padding:4px 10px; background:transparent; border:1px solid rgba(109,163,74,.5); color:rgba(109,163,74,.9); border-radius:4px; cursor:pointer; }
  .ctrl-bar .btn-flow:hover { background:rgba(109,163,74,.15); }
  .ctrl-bar .btn-flow.active { background:var(--green); color:var(--white); border-color:var(--green); }

  .screen { display:none; flex-direction:column; flex:1; }
  .screen.active { display:flex; }

  /* Notes */
  .notes-panel { display:none; background:#fffbeb; border-top:2px solid #f59e0b; padding:12px 20px; }
  .notes-panel.visible { display:block; }
  .notes-panel .notes-title { font-size:10px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:#92400e; margin-bottom:6px; }
  .notes-panel .note-main { font-size:14px; font-weight:600; color:#1c1917; line-height:1.5; }
  .notes-panel .note-deep { font-size:12px; color:#78716c; margin-top:4px; line-height:1.5; }

  /* Nav */
  .nav-bar { padding:12px 20px; display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--rule); background:var(--canvas); }
  .btn-nav { padding:10px 28px; font-size:14px; font-weight:700; border-radius:6px; cursor:pointer; border:none; }
  .btn-back { background:var(--white); border:1.5px solid var(--rule); color:var(--muted); }
  .btn-back:hover { border-color:var(--body); color:var(--body); }
  .btn-next { background:var(--green); color:var(--white); }
  .btn-next:hover { background:var(--green2); }
  .btn-inert { cursor:default !important; pointer-events:none !important; }

  /* SIGNiX bar */
  .signix-bar { background:var(--white); border-bottom:1px solid var(--rule); padding:8px 20px; display:flex; align-items:center; justify-content:space-between; }
  .signix-logo { font-size:22px; font-weight:900; letter-spacing:-.02em; color:var(--ink); }
  .signix-logo span { color:var(--green); }
  .signix-nav { display:flex; gap:20px; align-items:center; }
  .signix-nav a { font-size:13px; color:var(--blue); text-decoration:none; cursor:default; pointer-events:none; }
  .btn-logout { font-size:12px; padding:5px 14px; background:var(--ink); color:var(--white); border:none; border-radius:4px; cursor:default; font-weight:600; pointer-events:none; }

  /* Wizard tabs */
  .wizard-tabs { display:flex; justify-content:center; gap:4px; padding:14px 20px 0; background:var(--canvas); border-bottom:1px solid var(--rule); }
  .wizard-tab { padding:8px 20px; font-size:13px; font-weight:600; border:none; border-radius:6px 6px 0 0; cursor:default; background:#d1d5db; color:var(--muted); }
  .wizard-tab.active { background:var(--green); color:var(--white); }
  .wizard-tab.done   { background:#c6ddb5; color:var(--green2); }

  .content { flex:1; padding:20px; overflow-y:auto; }

  /* Dashboard */
  .dash-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
  .btn-create { padding:10px 20px; background:var(--green); color:var(--white); border:none; border-radius:6px; font-size:14px; font-weight:700; cursor:pointer; }
  .btn-create:hover { background:var(--green2); }
  .dash-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
  .dash-panel { border:1px solid var(--rule); border-radius:8px; overflow:hidden; }
  .dash-panel-header { padding:10px 14px; background:var(--canvas); border-bottom:1px solid var(--rule); font-size:13px; font-weight:700; color:var(--ink); }
  .dash-panel-body { padding:14px; }
  .dash-chart { height:80px; display:flex; align-items:flex-end; gap:8px; padding-bottom:8px; border-bottom:1px solid var(--rule); margin-bottom:8px; }
  .dash-bar-group { display:flex; flex-direction:column; align-items:center; flex:1; gap:4px; }
  .dash-bar { width:100%; background:var(--green); border-radius:3px 3px 0 0; opacity:.7; }
  .dash-bar-label { font-size:9px; color:var(--muted); text-align:center; }
  .dash-table { width:100%; border-collapse:collapse; }
  .dash-table th { font-size:11px; font-weight:700; color:var(--muted); text-align:left; padding:6px 8px; border-bottom:1px solid var(--rule); }
  .dash-table td { font-size:12px; padding:8px; border-bottom:1px solid var(--rule); }
  .dash-table td a { color:var(--blue); text-decoration:none; }
  .dash-status-badge { display:inline-block; font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px; background:#dcfce7; color:#166534; }
  .dash-status-badge.pending { background:#fef9c3; color:#854d0e; }
  .dash-status-badge.expired { background:#fee2e2; color:#991b1b; }

  /* Modal */
  .modal { background:var(--white); border-radius:8px; width:560px; max-width:95vw; box-shadow:0 20px 60px rgba(0,0,0,.2); overflow:hidden; }
  .modal-header { padding:16px 20px; font-size:18px; font-weight:700; color:var(--ink); border-bottom:1px solid var(--rule); display:flex; justify-content:space-between; align-items:center; }
  .modal-body { padding:20px; }
  .modal-footer { padding:14px 20px; background:var(--canvas); display:flex; justify-content:flex-end; gap:10px; border-top:1px solid var(--rule); }

  /* Forms */
  .form-row   { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:14px; }
  .form-row-2 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:14px; }
  .field label { display:block; font-size:12px; font-weight:600; color:var(--ink); margin-bottom:4px; }
  .field input,.field select { width:100%; padding:9px 12px; border:1.5px solid var(--rule); border-radius:6px; font-size:14px; color:var(--ink); background:var(--white); outline:none; }
  .field input:focus,.field select:focus { border-color:var(--green); }
  .checkbox-row { display:flex; gap:20px; margin-top:8px; }
  .checkbox-row label { display:flex; align-items:center; gap:6px; font-size:13px; color:var(--body); cursor:pointer; }
  .auth-badge { display:none; margin-top:8px; padding:8px 12px; background:#f0f7eb; border:1px solid var(--green); border-radius:6px; font-size:12px; color:var(--green2); font-weight:600; }
  .auth-badge.visible { display:block; }

  /* Buttons */
  .btn-sm { padding:5px 12px; font-size:12px; font-weight:700; border:none; border-radius:4px; cursor:pointer; }
  .btn-green { background:var(--green); color:var(--white); }
  .btn-outline-green { background:var(--white); border:1.5px solid var(--green); color:var(--green); }
  .btn-persona { background:var(--persona); color:var(--white); border:none; border-radius:8px; cursor:pointer; font-weight:700; }
  .btn-persona:hover { background:var(--persona2); }

  /* Documents tab */
  .upload-bar { display:flex; align-items:center; gap:14px; margin-bottom:16px; }
  .upload-hint { font-size:13px; color:var(--muted); }
  .doc-table { width:100%; border-collapse:collapse; }
  .doc-table th { font-size:11px; font-weight:700; color:var(--muted); text-align:left; padding:8px 12px; border-bottom:2px solid var(--rule); background:var(--canvas); }
  .doc-table td { font-size:13px; padding:12px; border-bottom:1px solid var(--rule); }
  .doc-icon { display:inline-block; width:24px; height:28px; background:#fee2e2; border-radius:3px; margin-right:8px; vertical-align:middle; font-size:9px; font-weight:700; color:var(--red); text-align:center; line-height:28px; }

  /* Send */
  .send-field { margin-bottom:16px; }
  .send-field label { display:block; font-size:13px; font-weight:600; color:var(--ink); margin-bottom:6px; }
  .send-field input,.send-field textarea { width:100%; padding:10px 14px; border:1.5px solid var(--rule); border-radius:6px; font-size:14px; color:var(--ink); outline:none; }
  .send-field textarea { min-height:80px; resize:vertical; }
  .demo-toggle { display:flex; gap:20px; align-items:center; }
  .radio-opt { display:flex; align-items:center; gap:6px; font-size:13px; cursor:pointer; }
  .expiry-note { font-size:12px; color:var(--muted); margin-top:8px; font-style:italic; }
  .send-actions { display:flex; justify-content:flex-end; gap:10px; margin-top:24px; }

  /* Email */
  .email-chrome { border:1px solid var(--rule); border-radius:8px; overflow:hidden; margin:0 auto; max-width:680px; }
  .email-header-bar { background:var(--canvas); padding:12px 16px; border-bottom:1px solid var(--rule); font-size:13px; color:var(--body); }
  .email-header-bar strong { color:var(--ink); }
  .email-body { padding:32px 40px; }
  .email-subject { font-size:18px; font-weight:700; color:var(--ink); margin-bottom:20px; }
  .email-text { font-size:14px; line-height:1.7; color:var(--body); margin-bottom:16px; }
  .btn-email-cta { display:block; width:100%; padding:14px; background:var(--green); color:var(--white); font-size:15px; font-weight:700; text-align:center; border:none; border-radius:6px; cursor:pointer; margin:24px 0; }
  .btn-email-cta:hover { background:var(--green2); }
  .email-footer { font-size:11px; color:var(--muted); border-top:1px solid var(--rule); padding-top:16px; line-height:1.6; }

  /* Consent */
  .consent-wrap { max-width:680px; margin:0 auto; }
  .consent-welcome { font-size:22px; font-weight:700; color:var(--green); margin-bottom:16px; }
  .consent-text { font-size:13px; line-height:1.7; color:var(--body); margin-bottom:20px; }
  .consent-question { font-size:14px; font-weight:600; color:var(--ink); margin-bottom:12px; }
  .consent-radios { display:flex; gap:24px; margin-bottom:20px; }
  .consent-radios label { display:flex; align-items:center; gap:8px; font-size:14px; cursor:pointer; }

  /* Auth challenge */
  .auth-wrap { max-width:520px; margin:0 auto; text-align:center; padding:20px 0; }
  .auth-icon { font-size:56px; margin-bottom:16px; }
  .auth-title { font-size:20px; font-weight:700; color:var(--ink); margin-bottom:8px; }
  .auth-sub { font-size:14px; color:var(--muted); margin-bottom:28px; line-height:1.6; }
  .auth-method-badge { display:inline-block; padding:8px 20px; background:#f0f7eb; border:2px solid var(--green); border-radius:8px; margin-bottom:24px; font-size:14px; font-weight:700; color:var(--green2); }
  .auth-input-group { text-align:left; margin-bottom:20px; }
  .auth-input-group label { display:block; font-size:13px; font-weight:600; color:var(--ink); margin-bottom:6px; }
  .auth-input-group input { width:100%; padding:12px; border:1.5px solid var(--rule); border-radius:6px; font-size:14px; outline:none; }
  .btn-verify { width:100%; padding:14px; background:var(--green); color:var(--white); font-size:15px; font-weight:700; border:none; border-radius:8px; cursor:pointer; }
  .btn-verify:hover { background:var(--green2); }
  .auth-disclaimer { max-width:520px; margin:16px auto 0; padding:12px 16px; background:#fffbeb; border:1px solid #f59e0b; border-radius:6px; font-size:12px; color:#92400e; line-height:1.6; text-align:left; }

  /* Persona flow screens */
  .persona-shell { flex:1; background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%); display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px; }
  .persona-card { background:var(--white); border-radius:12px; width:100%; max-width:420px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,.5); }
  .persona-card-header { padding:14px 20px; background:#f8fafc; border-bottom:1px solid #e2e8f0; display:flex; align-items:center; justify-content:space-between; }
  .persona-brand { font-size:13px; font-weight:800; color:#1a56db; letter-spacing:-.01em; }
  .persona-secure { font-size:11px; color:#64748b; display:flex; align-items:center; gap:4px; }
  .persona-card-body { padding:28px 24px 20px; }
  .persona-step-label { font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#64748b; margin-bottom:12px; }
  .persona-title { font-size:20px; font-weight:800; color:#0f172a; margin-bottom:10px; line-height:1.3; }
  .persona-subtitle { font-size:13px; color:#475569; line-height:1.6; margin-bottom:24px; }
  .persona-id-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px; }
  .persona-id-card { border:2px solid #e2e8f0; border-radius:8px; padding:14px 12px; text-align:center; cursor:pointer; transition:border-color .15s; }
  .persona-id-card.selected { border-color:#1a56db; background:#eff6ff; }
  .persona-id-card .id-icon { font-size:24px; margin-bottom:6px; }
  .persona-id-card .id-label { font-size:12px; font-weight:600; color:#1e293b; }
  .persona-camera-box { background:#0f172a; border-radius:10px; height:200px; display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:20px; position:relative; }
  .persona-camera-overlay { width:70%; height:75%; border:3px solid rgba(255,255,255,.7); border-radius:8px; display:flex; align-items:center; justify-content:center; }
  .persona-camera-hint { position:absolute; bottom:12px; font-size:12px; color:rgba(255,255,255,.7); }
  .persona-face-oval { width:140px; height:180px; border:3px solid rgba(255,255,255,.8); border-radius:50%; display:flex; align-items:center; justify-content:center; }
  .persona-face-icon { font-size:56px; color:rgba(255,255,255,.3); }
  .persona-input-row { margin-bottom:16px; }
  .persona-input-row label { display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px; }
  .persona-input-row input,.persona-input-row select { width:100%; padding:10px 14px; border:1.5px solid #d1d5db; border-radius:8px; font-size:14px; outline:none; }
  .persona-input-row input:focus { border-color:#1a56db; }
  .persona-dots { display:flex; justify-content:center; gap:6px; margin-bottom:16px; }
  .persona-dot { width:8px; height:8px; border-radius:50%; background:#d1d5db; }
  .persona-dot.done { background:#1a56db; }
  .persona-dot.current { background:#0f172a; }
  .persona-success-icon { font-size:52px; text-align:center; margin-bottom:16px; }
  .persona-country-search { width:100%; padding:10px 14px 10px 36px; border:1.5px solid #d1d5db; border-radius:8px; font-size:14px; outline:none; margin-bottom:16px; background:#f8fafc; }
  .persona-country-option { padding:10px 14px; border-radius:6px; font-size:14px; cursor:pointer; display:flex; align-items:center; gap:10px; }
  .persona-country-option.selected { background:#eff6ff; color:#1a56db; font-weight:600; }
  .btn-persona-primary { width:100%; padding:13px; background:#1a56db; color:var(--white); font-size:15px; font-weight:700; border:none; border-radius:8px; cursor:pointer; margin-top:4px; }
  .btn-persona-primary:hover { background:#1e40af; }
  .persona-footer { padding:12px 24px 16px; text-align:center; }
  .persona-footer-note { font-size:11px; color:#94a3b8; }

  /* Signature tagging screen */
  .tagging-shell { flex:1; background:#f1f5f9; display:flex; flex-direction:row; overflow:hidden; }
  .tagging-doc-area { flex:1; padding:16px; overflow-y:auto; }
  .tagging-sidebar { width:160px; background:var(--white); border-left:1px solid var(--rule); padding:12px; display:flex; flex-direction:column; gap:8px; overflow-y:auto; }
  .tagging-sidebar-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); margin-bottom:4px; }
  .tagging-field-btn { padding:9px 8px; border:1.5px dashed #94a3b8; border-radius:6px; text-align:center; font-size:12px; font-weight:600; color:var(--ink); background:var(--canvas); cursor:default; }
  .tagging-field-btn.active { border-color:var(--green); background:#f0f7eb; color:var(--green2); }
  .tagging-doc-page { background:var(--white); border:1px solid var(--rule); border-radius:6px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,.06); max-width:580px; margin:0 auto; }
  .tagging-sig-field { display:inline-block; background:#fef9c3; border:2px dashed #d97706; border-radius:4px; padding:4px 12px; font-size:12px; color:#92400e; font-weight:700; cursor:default; margin:4px; }
  .tagging-init-field { display:inline-block; background:#eff6ff; border:2px dashed #1a56db; border-radius:4px; padding:4px 10px; font-size:12px; color:#1e40af; font-weight:700; cursor:default; margin:4px; }
  .tagging-toolbar { background:var(--ink); padding:8px 16px; display:flex; align-items:center; gap:16px; }
  .tagging-toolbar-label { font-size:11px; color:rgba(255,255,255,.5); font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
  .tagging-signer-tag { font-size:12px; font-weight:700; padding:4px 12px; background:var(--green); color:var(--white); border-radius:12px; }

  /* SIGNiX ID-passed and Create Sig screens */
  .signix-result-wrap { max-width:580px; margin:0 auto; text-align:center; padding:20px 0; }
  .signix-result-icon { font-size:64px; margin-bottom:16px; }
  .signix-result-title { font-size:22px; font-weight:800; color:var(--ink); margin-bottom:10px; }
  .signix-result-sub { font-size:14px; color:var(--muted); line-height:1.7; margin-bottom:28px; }
  .signix-result-badge { display:inline-block; padding:8px 20px; background:#f0f7eb; border:2px solid var(--green); border-radius:8px; font-size:13px; font-weight:700; color:var(--green2); margin-bottom:24px; }
  .create-sig-card { max-width:560px; margin:0 auto; }
  .sig-style-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px; }
  .sig-style-opt { border:2px solid var(--rule); border-radius:8px; padding:12px 16px; text-align:center; cursor:pointer; }
  .sig-style-opt.selected { border-color:var(--green); background:#f0f7eb; }
  .sig-style-opt .sig-preview { font-size:22px; font-style:italic; color:var(--ink); font-family:Georgia,serif; margin-bottom:4px; }
  .sig-style-opt .sig-style-name { font-size:11px; color:var(--muted); }

  /* Document signing */
  .signing-wrap { max-width:720px; margin:0 auto; }
  .progress-bar-wrap { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
  .progress-label { font-size:12px; font-weight:700; color:var(--muted); }
  .progress-track { flex:1; height:8px; background:var(--rule); border-radius:4px; overflow:hidden; }
  .progress-fill { height:100%; background:var(--green); border-radius:4px; }
  .doc-header { text-align:center; margin-bottom:20px; }
  .doc-title-line { font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--ink); margin-top:8px; }
  .doc-body-text { font-size:13px; line-height:1.8; color:var(--body); margin-bottom:16px; }
  .doc-body-text ol { padding-left:20px; }
  .doc-body-text ol li { margin-bottom:10px; }
  .required-field { background:var(--yellow); border:2px solid #d97706; border-radius:4px; padding:8px 12px; margin-bottom:16px; display:flex; align-items:center; gap:12px; }
  .required-label { font-size:11px; font-weight:800; text-transform:uppercase; color:#92400e; white-space:nowrap; }
  .required-input { flex:1; border:none; background:transparent; font-size:14px; color:var(--ink); font-weight:600; outline:none; }
  .sig-block { border-top:1px solid var(--rule); padding-top:16px; margin-top:8px; }
  .sig-row { display:grid; grid-template-columns:1fr auto 1fr; gap:16px; align-items:end; margin-bottom:12px; }
  .sig-field label { font-size:12px; color:var(--muted); display:block; margin-bottom:4px; }
  .sig-line { border-bottom:1.5px solid var(--ink); padding:6px 0; font-size:15px; font-family:Georgia,serif; color:var(--ink); min-height:32px; }
  .sig-line.signed { font-style:italic; }
  .sig-badge { font-size:10px; font-weight:700; background:var(--green); color:var(--white); padding:2px 8px; border-radius:4px; }
  .name-field { border-bottom:1.5px solid var(--ink); padding:6px 0; font-size:14px; font-weight:600; color:var(--ink); }
  .finish-title { font-size:20px; font-weight:700; color:var(--ink); margin-bottom:12px; }
  .finish-text  { font-size:13px; line-height:1.7; color:var(--body); margin-bottom:24px; }
  .finish-btns  { display:flex; justify-content:flex-end; gap:10px; }

  /* Confirmation */
  .confirm-wrap { max-width:640px; margin:20px auto; }
  .confirm-title { font-size:22px; font-weight:700; color:var(--green); margin-bottom:12px; }
  .confirm-text  { font-size:14px; line-height:1.7; color:var(--body); margin-bottom:8px; }
  .confirm-grid  { display:grid; grid-template-columns:1fr auto; gap:24px; align-items:start; margin-top:16px; }
  .confirm-qr-block { text-align:center; min-width:150px; }
  .confirm-qr-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); margin-bottom:8px; }
  .confirm-qr-contact { font-size:12px; color:var(--body); margin-top:10px; line-height:1.8; }
  .confirm-qr-contact strong { color:var(--ink); }

  /* Signer list */
  .signer-row { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:#f0f7eb; border:1.5px solid var(--green); border-radius:8px; margin-bottom:8px; }
  .signer-info { display:flex; flex-direction:column; gap:2px; }
  .signer-name  { font-size:14px; font-weight:700; color:var(--ink); }
  .signer-email { font-size:12px; color:var(--muted); }
  .signer-auth-tag { font-size:11px; font-weight:700; padding:3px 10px; background:var(--green); color:var(--white); border-radius:12px; }

  @media (max-width:640px) {
    .dash-grid { grid-template-columns:1fr; }
    .form-row,.form-row-2 { grid-template-columns:1fr; }
    .sig-row { grid-template-columns:1fr; }
    .email-body { padding:20px; }
    .confirm-grid { grid-template-columns:1fr; }
    .tagging-shell { flex-direction:column; }
    .tagging-sidebar { width:100%; flex-direction:row; flex-wrap:wrap; }
  }
"""

# ── Persona progress dots ──────────────────────────────────────────────────────
def pdots(current_idx, total=9):
    dots = ""
    for i in range(total):
        cls = "done" if i < current_idx else ("current" if i == current_idx else "")
        dots += f'<div class="persona-dot {cls}"></div>'
    return f'<div class="persona-dots">{dots}</div>'

# ── Build HTML ─────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
<title>SIGNiX MyDox — Interactive Demo v2</title>
<style>{CSS}</style>
</head>
<body>
<div class="demo-shell">

  <!-- Control bar -->
  <div class="ctrl-bar">
    <span class="demo-label">MyDox Live Demo</span>
    <span class="step-counter" id="step-counter">Step 1 of 14</span>
    <div style="display:flex;gap:6px;">
      <button class="btn-notes" onclick="toggleNotes()">&#9776; Notes</button>
      <button class="btn-flow" id="btn-flow" onclick="toggleFlow()">Full Flow</button>
      <button class="btn-reset" onclick="resetDemo()">&#8635; Restart</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 1 — Dashboard
  ══════════════════════════════════════════════════════════ -->
  <div class="screen active" id="screen-1">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div class="signix-nav">
        <span style="font-size:13px;color:var(--body);">MyDoX Sandbox — Workgroup</span>
        <select style="font-size:13px;padding:3px 8px;border:1px solid var(--rule);border-radius:4px;color:var(--blue);pointer-events:none;"><option>Corporate Administrator</option></select>
        <a>Dashboard</a><a>Transactions</a><a>Templates</a><a>Mass Mailer</a><a>ENotary Profile</a>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="content">
      <div class="dash-header">
        <div style="font-size:16px;font-weight:700;color:var(--ink);">Dashboard</div>
        <button class="btn-create" onclick="goTo(2)">Create New Transaction</button>
      </div>
      <div class="dash-grid">
        <div class="dash-panel">
          <div class="dash-panel-header">Transactions by Status</div>
          <div class="dash-panel-body">
            <div class="dash-chart">
              <div class="dash-bar-group"><div class="dash-bar" style="height:60px;"></div><div class="dash-bar-label">All</div></div>
              <div class="dash-bar-group"><div class="dash-bar" style="height:40px;background:#166534;"></div><div class="dash-bar-label">Complete</div></div>
              <div class="dash-bar-group"><div class="dash-bar" style="height:25px;background:#2563eb;"></div><div class="dash-bar-label">In Process</div></div>
              <div class="dash-bar-group"><div class="dash-bar" style="height:10px;background:#dc2626;"></div><div class="dash-bar-label">Expired</div></div>
              <div class="dash-bar-group"><div class="dash-bar" style="height:5px;background:#6b7280;"></div><div class="dash-bar-label">Cancelled</div></div>
            </div>
          </div>
        </div>
        <div class="dash-panel">
          <div class="dash-panel-header">Recently Updated Transactions</div>
          <div class="dash-panel-body">
            <table class="dash-table">
              <thead><tr><th>Name</th><th>Status</th><th>Last Modified</th></tr></thead>
              <tbody>
                <tr><td><a>County Vendor Agreement</a></td><td><span class="dash-status-badge pending">1 of 2</span></td><td style="font-size:11px;color:var(--muted);">2 hours ago</td></tr>
                <tr><td><a>Dept. Access Authorization</a></td><td><span class="dash-status-badge">Complete</span></td><td style="font-size:11px;color:var(--muted);">Apr 13</td></tr>
                <tr><td><a>HR Acknowledgement Form</a></td><td><span class="dash-status-badge expired">Expired</span></td><td style="font-size:11px;color:var(--muted);">Apr 12</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="dash-panel">
          <div class="dash-panel-header">Recently Completed Transactions</div>
          <div class="dash-panel-body">
            <table class="dash-table">
              <thead><tr><th>Name</th><th>Last Modified</th><th></th></tr></thead>
              <tbody>
                <tr><td><a>Procurement Contract Q1</a></td><td style="font-size:11px;color:var(--muted);">Apr 8</td><td><button class="btn-sm btn-green btn-inert">Download</button></td></tr>
                <tr><td><a>Benefits Enrollment 2026</a></td><td style="font-size:11px;color:var(--muted);">Mar 30</td><td><button class="btn-sm btn-green btn-inert">Download</button></td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="dash-panel">
          <div class="dash-panel-header">Recently Updated Templates</div>
          <div class="dash-panel-body">
            <table class="dash-table">
              <thead><tr><th>Name</th><th>Last Modified</th></tr></thead>
              <tbody>
                <tr><td><a>Standard Vendor Agreement</a></td><td style="font-size:11px;color:var(--muted);">2 hours ago</td></tr>
                <tr><td><a>3-Party Authorization</a></td><td style="font-size:11px;color:var(--muted);">Apr 6</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-1">
      <div class="notes-title">Speaker Notes — Screen 1: Dashboard</div>
      <div class="note-main">"This is where every transaction lives. No paper trail to lose — every document is tracked, timestamped, and accessible from one place."</div>
      <div class="note-deep">For Pem: Lead with simplicity. For Aspen: Note the status column — departments can see exactly where every document is in real time.</div>
    </div>
    <div class="nav-bar">
      <div></div>
      <button class="btn-nav btn-next" onclick="goTo(2)">Create New Transaction &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 2 — Add Signer
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-2">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-sm btn-green btn-inert" style="font-size:12px;">Save</button>
        <button class="btn-sm btn-outline-green btn-inert" style="font-size:12px;">Save As</button>
        <button class="btn-sm btn-inert" style="background:var(--canvas);border:1px solid var(--rule);font-size:12px;">Home</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="wizard-tabs">
      <div class="wizard-tab active">Signers</div>
      <div class="wizard-tab">Documents</div>
      <div class="wizard-tab">Signatures</div>
      <div class="wizard-tab">Send</div>
      <div class="wizard-tab">Status</div>
    </div>
    <div class="content">
      <div style="margin-bottom:12px;display:flex;gap:8px;">
        <button class="btn-sm btn-green btn-inert">Add New Signer</button>
        <button class="btn-sm btn-outline-green btn-inert">CC List</button>
        <button class="btn-sm btn-outline-green btn-inert">Address Book</button>
      </div>
      <table class="doc-table">
        <thead><tr><th>Order</th><th>Role</th><th>Name</th><th>Email</th><th>CC</th></tr></thead>
        <tbody><tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px;font-size:13px;font-style:italic;">No signers added yet</td></tr></tbody>
      </table>
      <div class="modal" style="max-width:560px;margin:20px auto;border:1px solid var(--rule);border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1);">
        <div class="modal-header" style="background:var(--canvas);">Signer Information</div>
        <div class="modal-body">
          <div class="form-row">
            <div class="field"><label>First</label><input type="text" id="signer-first" placeholder="Jane" oninput="updateSignerName()" /></div>
            <div class="field"><label>Middle</label><input type="text" placeholder="" /></div>
            <div class="field"><label>Last</label><input type="text" id="signer-last" placeholder="Smith" oninput="updateSignerName()" /></div>
          </div>
          <div class="form-row-2">
            <div class="field"><label>Email</label><input type="email" id="signer-email" placeholder="jane.smith@lacounty.gov" /></div>
            <div class="field"><label>Role</label><select><option>Signer</option><option>Approver</option><option>CC</option></select></div>
            <div class="field">
              <label>Authentication</label>
              <select id="auth-select" onchange="handleAuthChange()">
                <option value="">Select...</option>
                <option value="password">Password Only</option>
                <option value="2fa">2 Factor Authentication (Text Message)</option>
                <option value="kba">KBA-ID — Knowledge-based Questions with ID Verify SSN4</option>
                <option value="idverify">ID Verify — Credential Analysis &amp; Biometrics</option>
              </select>
              <div class="auth-badge" id="auth-badge">
                &#10003; Highest assurance — Credential Analysis &amp; Biometrics selected.<br>
                <span style="font-weight:400;font-size:11px;">Signer will verify a government-issued ID before signing.</span>
              </div>
            </div>
          </div>
          <div class="checkbox-row">
            <label><input type="checkbox" id="chk-i-am-signer" onchange="iAmTheSigner(this.checked)" /> I Am The Signer</label>
            <label><input type="checkbox" class="btn-inert" /> Use Placeholder Info</label>
            <label><input type="checkbox" class="btn-inert" /> Add To Address Book</label>
            <label><input type="checkbox" class="btn-inert" /> Notary</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-sm btn-outline-green btn-inert">Address Book</button>
          <button class="btn-sm btn-green" onclick="addSignerAndAdvance()">Add Signer</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-2">
      <div class="notes-title">Speaker Notes — Screen 2: Add Signer</div>
      <div class="note-main">"Fill in the signer's name and email — then choose how they authenticate. This is where most e-sign platforms stop. We require identity verification before anyone signs."</div>
      <div class="note-deep">For Aspen: Select "ID Verify" and show the green badge. For ABS reps: Check "I Am The Signer" to auto-fill demo info quickly.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(1)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="addSignerAndAdvance()">Add Signer &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 3 — Signer Confirmed
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-3">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-sm btn-green btn-inert" style="font-size:12px;">Save</button>
        <button class="btn-sm btn-outline-green btn-inert" style="font-size:12px;">Save As</button>
        <button class="btn-sm btn-inert" style="background:var(--canvas);border:1px solid var(--rule);font-size:12px;">Home</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="wizard-tabs">
      <div class="wizard-tab done">Signers</div>
      <div class="wizard-tab active">Documents</div>
      <div class="wizard-tab">Signatures</div>
      <div class="wizard-tab">Send</div>
      <div class="wizard-tab">Status</div>
    </div>
    <div class="content">
      <div style="margin-bottom:12px;display:flex;gap:8px;">
        <button class="btn-sm btn-green btn-inert">Add New Signer</button>
        <button class="btn-sm btn-outline-green btn-inert">CC List</button>
        <button class="btn-sm btn-outline-green btn-inert">Address Book</button>
      </div>
      <div class="signer-row">
        <div class="signer-info">
          <div class="signer-name" id="signer-display-name">Jane Smith</div>
          <div class="signer-email" id="signer-display-email">jane.smith@lacounty.gov</div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="signer-auth-tag" id="signer-display-auth">ID Verify</div>
          <div style="font-size:11px;color:var(--muted);">Order 1 — Signer</div>
        </div>
      </div>
      <div style="font-size:13px;color:var(--muted);font-style:italic;">Signer added. Proceed to upload your document.</div>
    </div>
    <div class="notes-panel" id="notes-3">
      <div class="notes-title">Speaker Notes — Screen 3: Signer Confirmed</div>
      <div class="note-main">"The signer is set. The authentication method is locked in — they can't bypass it. Every signing event is tied to a verified identity."</div>
      <div class="note-deep">For Aspen: Ask DocuSign prospects if DocuSign shows who authenticated and how. For Pem: "Before anyone signs, we know exactly who they are."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(2)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(4)">Upload Document &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 4 — Documents
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-4">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-sm btn-green btn-inert" style="font-size:12px;">Save</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="wizard-tabs">
      <div class="wizard-tab done">Signers</div>
      <div class="wizard-tab active">Documents</div>
      <div class="wizard-tab">Signatures</div>
      <div class="wizard-tab">Send</div>
      <div class="wizard-tab">Status</div>
    </div>
    <div class="content">
      <div class="upload-bar">
        <button class="btn-sm btn-green btn-inert">Upload Documents</button>
        <span class="upload-hint">Click the button or drag and drop files from your computer here</span>
      </div>
      <table class="doc-table">
        <thead><tr><th>Order</th><th>Document Name</th></tr></thead>
        <tbody>
          <tr>
            <td style="color:var(--muted);font-size:13px;">1</td>
            <td><span class="doc-icon">PDF</span>County_Vendor_Services_Agreement_2026.pdf <span style="font-size:11px;color:var(--green);margin-left:8px;font-weight:700;">&#10003; Ready</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="notes-panel" id="notes-4">
      <div class="notes-title">Speaker Notes — Screen 4: Documents</div>
      <div class="note-main">"Upload any document — contracts, authorizations, HR forms, vendor agreements. The system works for every department, not just one workflow."</div>
      <div class="note-deep">For Aspen: "What other departments in your county handle signed documents today?" For Pem: "Any document. Any department."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(3)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(5)">Tag Signature Fields &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 5 — Signature Tagging (NEW)
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-5">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-sm btn-green btn-inert" style="font-size:12px;">Save</button>
        <button class="btn-sm btn-outline-green btn-inert" style="font-size:12px;">Save As</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="wizard-tabs">
      <div class="wizard-tab done">Signers</div>
      <div class="wizard-tab done">Documents</div>
      <div class="wizard-tab active">Signatures</div>
      <div class="wizard-tab">Send</div>
      <div class="wizard-tab">Status</div>
    </div>
    <div class="tagging-toolbar">
      <span class="tagging-toolbar-label">Field Toolbar</span>
      <span class="tagging-signer-tag">Signer 1 — Jane Smith</span>
      <span style="font-size:11px;color:rgba(255,255,255,.4);margin-left:auto;">Drag fields onto the document</span>
    </div>
    <div class="tagging-shell">
      <div class="tagging-doc-area">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:12px;">Page 1 of 3 &mdash; County_Vendor_Services_Agreement_2026.pdf</div>
        <div class="tagging-doc-page">
          <div style="text-align:center;margin-bottom:20px;">
            <div style="font-size:14px;font-weight:900;color:var(--blue);">Los Angeles County</div>
            <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink);margin-top:6px;">Vendor Services Agreement — 2026</div>
          </div>
          <div style="font-size:12px;line-height:1.8;color:var(--body);margin-bottom:16px;">
            <p style="margin-bottom:12px;">This Vendor Services Agreement ("Agreement") is entered into as of the date of execution by and between <strong>Los Angeles County</strong> ("County") and the undersigned Vendor.</p>
            <p style="margin-bottom:12px;">1. The Vendor agrees to provide services as described in Exhibit A, incorporated herein by reference. All services shall be performed in compliance with applicable federal, state, and local laws.</p>
            <p style="margin-bottom:12px;">2. The County reserves the right to audit all records related to services performed under this agreement upon reasonable notice. This agreement is subject to Board of Supervisors approval.</p>
          </div>
          <div style="border-top:1px solid var(--rule);padding-top:16px;margin-top:8px;">
            <div style="font-size:12px;color:var(--muted);margin-bottom:12px;font-style:italic;">Signature fields placed for Signer 1 — Jane Smith (ID Verify required)</div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
              <span style="font-size:12px;color:var(--body);min-width:80px;">Signature:</span>
              <span class="tagging-sig-field">&#x270D; SIGNATURE · Signer 1</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
              <span style="font-size:12px;color:var(--body);min-width:80px;">Initial:</span>
              <span class="tagging-init-field">INI · Signer 1</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
              <span style="font-size:12px;color:var(--body);min-width:80px;">Date:</span>
              <span style="display:inline-block;background:#f0f7eb;border:2px dashed var(--green);border-radius:4px;padding:4px 12px;font-size:12px;color:var(--green2);font-weight:700;">DATE · auto</span>
            </div>
          </div>
        </div>
      </div>
      <div class="tagging-sidebar">
        <div class="tagging-sidebar-label">Fields</div>
        <div class="tagging-field-btn active">&#x270D; Signature</div>
        <div class="tagging-field-btn">INI Initial</div>
        <div class="tagging-field-btn">&#x1F4C5; Date</div>
        <div class="tagging-field-btn">T Text</div>
        <div class="tagging-field-btn">&#9744; Check</div>
        <div class="tagging-field-btn">&#x1F4CB; Acknowledge</div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--rule);">
          <div class="tagging-sidebar-label">Signers</div>
          <div style="font-size:11px;padding:6px 8px;background:#f0f7eb;border-radius:4px;color:var(--green2);font-weight:700;">1 · Jane Smith</div>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-5">
      <div class="notes-title">Speaker Notes — Screen 5: Signature Tagging</div>
      <div class="note-main">"You place signature and initial fields exactly where they belong on the document. Drag from the toolbar on the left, drop on the page."</div>
      <div class="note-deep">For Aspen: Show the left toolbar — Signature, Initial, Date, Text, Checkbox. For ABS reps: You define where each signer signs. The system guides the signer to these fields automatically. For Pem: "No printing. No scanning. Every field is tracked."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(4)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(6)">Configure &amp; Send &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 6 — Send
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-6">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-sm btn-green btn-inert" style="font-size:12px;">Save</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="wizard-tabs">
      <div class="wizard-tab done">Signers</div>
      <div class="wizard-tab done">Documents</div>
      <div class="wizard-tab done">Signatures</div>
      <div class="wizard-tab active">Send</div>
      <div class="wizard-tab">Status</div>
    </div>
    <div class="content">
      <div class="send-field"><label>Title</label><input type="text" value="County Vendor Services Agreement — 2026" /></div>
      <div class="send-field">
        <label>Demonstration Mode?</label>
        <div class="demo-toggle">
          <label class="radio-opt"><input type="radio" name="demo" checked /> Yes</label>
          <label class="radio-opt"><input type="radio" name="demo" /> No</label>
        </div>
      </div>
      <div class="send-field"><label>Email Message</label><textarea>Please review and sign the attached document at your earliest convenience. This agreement requires identity verification before signing.</textarea></div>
      <div class="send-field">
        <label>Reminders / Expiration Schedule</label>
        <input type="range" min="3" max="30" value="10" style="width:100%;" />
        <div class="expiry-note">The documents will expire after 10 day(s), and signer(s) will receive reminders on day(s) 3 and 7</div>
        <label style="font-size:13px;margin-top:8px;display:flex;align-items:center;gap:6px;cursor:pointer;"><input type="checkbox" /> I do not want to send reminders to signer(s)</label>
      </div>
      <div class="send-actions">
        <button class="btn-sm btn-outline-green btn-inert" style="padding:10px 20px;font-size:13px;">Sign Now</button>
        <button class="btn-sm btn-green" style="padding:10px 20px;font-size:13px;" onclick="goTo(7)">Send</button>
      </div>
    </div>
    <div class="notes-panel" id="notes-6">
      <div class="notes-title">Speaker Notes — Screen 6: Send</div>
      <div class="note-main">"Set the expiration, add a message, and send. The signer gets an email within seconds."</div>
      <div class="note-deep">For Aspen: Point out Demonstration Mode. For Pem: "From upload to sent in under two minutes."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(5)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(7)">Send &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 7 — Signer Email
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-7">
    <div class="content" style="background:#f1f5f9;">
      <div class="email-chrome">
        <div class="email-header-bar">
          <strong>From:</strong> Signix Online Signatures &lt;noreply@signixmail.com&gt;<br>
          <strong>To:</strong> <span id="email-to-name">Jane Smith</span><br>
          <strong>Subject:</strong> Your Documents are Ready — County Vendor Services Agreement 2026<br>
          <span style="font-size:11px;color:var(--muted);">Retention: Compliance Expires 04/15/2033</span>
        </div>
        <div class="email-body">
          <div class="email-subject">Your Documents Are Ready to Sign</div>
          <div class="email-text">Hello <span id="email-greeting-name">Jane</span>!</div>
          <div class="email-text">This is from LA County using SIGNiX to deliver documents to you for your review and signature.</div>
          <div class="email-text">Click the button below to access your documents.</div>
          <button class="btn-email-cta" onclick="goTo(8)">Review &amp; Sign Documents</button>
          <div class="email-text">Thank you,<br>LA County — Procurement Division</div>
          <div class="email-footer">You received this email because you have been sent documents to review, fill, and/or sign by a person or organization using the SIGNiX electronic signature service.<br><br>SIGNIX, Inc. &nbsp;·&nbsp; www.signix.com &nbsp;·&nbsp; 1110 Market Street, Suite 403 · Chattanooga, TN 37402</div>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-7">
      <div class="notes-title">Speaker Notes — Screen 7: Signer Email</div>
      <div class="note-main">"This is what your signer receives. Branded, clear, one button. Works on any device."</div>
      <div class="note-deep">For Aspen: Note the 2033 compliance expiration — 7-year retention baked in. For Pem: "The signer doesn't need an account. They click one button."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(6)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(8)">Signer Opens Email &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 8 — Legal Consent
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-8">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content">
      <div class="consent-wrap">
        <div class="consent-welcome">Welcome, <span id="consent-name">Jane Smith</span>!</div>
        <div class="consent-text">You've been asked to review and sign documents online. It's easy!</div>
        <div class="consent-text">To get started, agree to receive electronic documents under the terms of the E-Sign Legal Consent by choosing Accept below.</div>
        <div class="consent-text">Click Next to continue!</div>
        <div class="consent-question">Agree to Legal Consent and Terms of Service?</div>
        <div class="consent-radios">
          <label><input type="radio" name="consent" checked /> Accept</label>
          <label><input type="radio" name="consent" /> Decline</label>
        </div>
        <button class="btn-sm btn-outline-green btn-inert" style="padding:8px 16px;">Read Legal Consent</button>
      </div>
    </div>
    <div class="notes-panel" id="notes-8">
      <div class="notes-title">Speaker Notes — Screen 8: Legal Consent</div>
      <div class="note-main">"Before a single field is filled, we capture legal consent. E-Sign Act compliance baked in — not an add-on."</div>
      <div class="note-deep">For Aspen: The consent is timestamped in the audit trail. If a document is challenged, you can prove the signer agreed. For Pem: "Every county is exposed if a signed document gets challenged. This is how we protect them."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(7)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(9)">Accept &amp; Continue &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 9 — ID Verify Intro
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-9">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content">
      <div class="auth-wrap">
        <div class="auth-icon">&#x1F6C2;</div>
        <div class="auth-title"><span id="auth-name">Jane</span>, Identity Verification Required</div>
        <div class="auth-sub">This document requires identity verification before you can sign. Your information is encrypted and used only to confirm your identity.</div>
        <div class="auth-method-badge">ID Verify — Credential Analysis &amp; Biometrics</div>
        <div class="auth-input-group">
          <label>Government-Issued ID Number (last 4 digits)</label>
          <input type="text" placeholder="••••" maxlength="4" value="4892" />
        </div>
        <div class="auth-input-group">
          <label>Date of Birth</label>
          <input type="text" placeholder="MM/DD/YYYY" value="••/••/••••" />
        </div>
        <button class="btn-verify" onclick="goToAfterIDVerify()">Verify My Identity &amp; Proceed</button>
      </div>
      <div class="auth-disclaimer">
        <strong>&#9432; About ID Verify:</strong> In a live transaction, SIGNiX launches a secure identity verification flow powered by Persona. The signer scans a government-issued ID and completes a real-time biometric liveness check. Verification takes under 60 seconds. Toggle <strong>Full Flow</strong> in the control bar above to walk through every step.
      </div>
    </div>
    <div class="notes-panel" id="notes-9">
      <div class="notes-title">Speaker Notes — Screen 9: ID Verify</div>
      <div class="note-main">"This is where SIGNiX separates from every other platform. Before anyone signs, we verify who they are. That signature is tied to a real, verified identity."</div>
      <div class="note-deep">For Aspen: "What happens if someone disputes the signature?" Show this screen. For Pem: "No other vendor in this room can show you this screen." For ABS reps: Toggle Full Flow to walk through every step the signer experiences.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(8)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goToAfterIDVerify()">Identity Verified &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 10 — Persona: Getting Started  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-10">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(0)}
          <div class="persona-step-label">Identity Verification · Step 1 of 9</div>
          <div class="persona-title">Let's verify your identity</div>
          <div class="persona-subtitle">To complete your request, we need to verify your identity. This process is quick and secure. Your data is used only to confirm who you are.</div>
          <div style="background:#eff6ff;border-radius:8px;padding:12px 14px;margin-bottom:20px;">
            <div style="font-size:12px;font-weight:700;color:#1e40af;margin-bottom:4px;">What you'll need:</div>
            <div style="font-size:13px;color:#1e3a8a;line-height:1.6;">&#10003; A government-issued photo ID<br>&#10003; A smartphone or camera<br>&#10003; Good lighting</div>
          </div>
          <div class="persona-footer-note" style="margin-bottom:16px;">By continuing you agree to Persona's <a style="color:#1a56db;">Privacy Policy</a> and <a style="color:#1a56db;">Terms of Use</a></div>
          <button class="btn-persona-primary" onclick="goTo(11)">Get Started</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-10">
      <div class="notes-title">Speaker Notes — Screen 10: Persona Consent [Full Flow]</div>
      <div class="note-main">"The signer consents to Persona — SIGNiX's credential analysis partner. This consent is logged in the audit trail."</div>
      <div class="note-deep">For ABS reps: Persona is the leading identity verification platform powering hundreds of financial institutions. SIGNiX routes the signer here automatically when ID Verify is selected.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(9)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(11)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 11 — Persona: Country  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-11">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(1)}
          <div class="persona-step-label">Identity Verification · Step 2 of 9</div>
          <div class="persona-title">What country issued your ID?</div>
          <div class="persona-subtitle">Select the country that issued your government photo ID.</div>
          <div style="position:relative;margin-bottom:12px;">
            <span style="position:absolute;left:12px;top:12px;color:#94a3b8;">&#x1F50D;</span>
            <input class="persona-country-search" placeholder="Search countries..." value="United States" />
          </div>
          <div class="persona-country-option selected">&#127482;&#127480; United States</div>
          <div class="persona-country-option">&#127464;&#127462; Canada</div>
          <div class="persona-country-option">&#127468;&#127463; United Kingdom</div>
          <div class="persona-country-option" style="color:#94a3b8;font-size:13px;padding:6px 14px;">&#8943; 190+ countries supported</div>
          <button class="btn-persona-primary" style="margin-top:16px;" onclick="goTo(12)">Continue</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-11">
      <div class="notes-title">Speaker Notes — Screen 11: Country Selection [Full Flow]</div>
      <div class="note-main">"The signer selects where their ID was issued. SIGNiX supports international documents — not just U.S. IDs."</div>
      <div class="note-deep">For ABS reps: This matters for institutions with international customers. 190+ countries are supported automatically.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(10)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(12)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 12 — Persona: ID Type  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-12">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(2)}
          <div class="persona-step-label">Identity Verification · Step 3 of 9</div>
          <div class="persona-title">Upload a photo ID</div>
          <div class="persona-subtitle">Select the type of government-issued photo ID you'll use.</div>
          <div class="persona-id-grid">
            <div class="persona-id-card selected"><div class="id-icon">&#x1F4CB;</div><div class="id-label">Driver License</div></div>
            <div class="persona-id-card"><div class="id-icon">&#x1F6C2;</div><div class="id-label">State ID</div></div>
            <div class="persona-id-card"><div class="id-icon">&#x1F4D4;</div><div class="id-label">Passport</div></div>
            <div class="persona-id-card"><div class="id-icon">&#x1F4C4;</div><div class="id-label">Passport Card</div></div>
          </div>
          <button class="btn-persona-primary" onclick="goTo(13)">Continue with Driver License</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-12">
      <div class="notes-title">Speaker Notes — Screen 12: ID Type [Full Flow]</div>
      <div class="note-main">"The signer picks their ID type. Driver's license, passport, state ID — the system handles all of them."</div>
      <div class="note-deep">For ABS reps: No special hardware needed. The signer uses their phone camera. Verification works on any modern device.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(11)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(13)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 13 — Persona: Expiry Date  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-13">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(3)}
          <div class="persona-step-label">Identity Verification · Step 4 of 9</div>
          <div class="persona-title">Enter your expiration date</div>
          <div class="persona-subtitle">Enter the expiration date on the front of your Driver License. Expired IDs will be rejected.</div>
          <div class="persona-input-row">
            <label>Expiration Date</label>
            <input type="text" placeholder="MM / YYYY" value="09 / 2028" />
          </div>
          <div style="background:#f8fafc;border-radius:8px;padding:10px 14px;font-size:12px;color:#64748b;margin-bottom:16px;">
            &#128274; This information is encrypted. It is never shared with third parties.
          </div>
          <button class="btn-persona-primary" onclick="goTo(14)">Continue</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-13">
      <div class="notes-title">Speaker Notes — Screen 13: Expiry Date [Full Flow]</div>
      <div class="note-main">"The system confirms the ID is not expired before proceeding. Expired documents are rejected automatically."</div>
      <div class="note-deep">For ABS reps: This is the first of several validation checks. The system is verifying document validity before image capture even begins.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(12)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(14)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 14 — Persona: Front of ID  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-14">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(4)}
          <div class="persona-step-label">Identity Verification · Step 5 of 9</div>
          <div class="persona-title">Take a photo of the front of your ID</div>
          <div class="persona-subtitle">Position your Driver License in the frame below and tap the button to capture.</div>
          <div class="persona-camera-box">
            <div class="persona-camera-overlay">
              <div style="text-align:center;color:rgba(255,255,255,.5);">
                <div style="font-size:28px;margin-bottom:6px;">&#x1F4CB;</div>
                <div style="font-size:11px;">Align ID within frame</div>
              </div>
            </div>
            <div class="persona-camera-hint">Ensure text is clear and all four corners are visible</div>
          </div>
          <button class="btn-persona-primary" onclick="goTo(15)">&#128247; Capture Front of ID</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-14">
      <div class="notes-title">Speaker Notes — Screen 14: Front of ID [Full Flow]</div>
      <div class="note-main">"The signer photographs the front of their ID. The system checks the image is clear enough to read before accepting it."</div>
      <div class="note-deep">For ABS reps: Persona's credential analysis engine checks for tampering, font consistency, and security features. Not a simple OCR scan — it's a deep document analysis.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(13)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(15)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 15 — Persona: Back of ID  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-15">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(5)}
          <div class="persona-step-label">Identity Verification · Step 6 of 9</div>
          <div class="persona-title">Now take a photo of the back</div>
          <div class="persona-subtitle">Flip your Driver License over and photograph the back side. The barcode will be scanned and verified.</div>
          <div class="persona-camera-box">
            <div class="persona-camera-overlay">
              <div style="text-align:center;color:rgba(255,255,255,.5);">
                <div style="font-size:28px;margin-bottom:6px;">&#x1F4CB;</div>
                <div style="font-size:11px;">Barcode must be visible</div>
              </div>
            </div>
            <div class="persona-camera-hint">Back side — barcode will be cross-referenced with front data</div>
          </div>
          <button class="btn-persona-primary" onclick="goTo(16)">&#128247; Capture Back of ID</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-15">
      <div class="notes-title">Speaker Notes — Screen 15: Back of ID [Full Flow]</div>
      <div class="note-main">"The barcode on the back is read and cross-referenced with the front. If they don't match, the ID fails."</div>
      <div class="note-deep">For ABS reps: This catches altered documents. The barcode data must be consistent with the printed fields on the front. Most fraudulent IDs fail here.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(14)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(16)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 16 — Persona: Liveness Check  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-16">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(6)}
          <div class="persona-step-label">Identity Verification · Step 7 of 9</div>
          <div class="persona-title">Let's make sure you're you</div>
          <div class="persona-subtitle">We'll take a short selfie video to confirm you are physically present — not a photo or recording. This defeats impersonation and deepfake attempts.</div>
          <div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:12px 14px;margin-bottom:20px;">
            <div style="font-size:12px;font-weight:700;color:#92400e;margin-bottom:4px;">Before you begin:</div>
            <div style="font-size:13px;color:#78716c;line-height:1.6;">
              &#10003; Find good lighting — face should be clearly visible<br>
              &#10003; Remove sunglasses and hats<br>
              &#10003; Look directly at the camera
            </div>
          </div>
          <button class="btn-persona-primary" onclick="goTo(17)">&#x1F4F7; Start Selfie Check</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-16">
      <div class="notes-title">Speaker Notes — Screen 16: Liveness Check [Full Flow]</div>
      <div class="note-main">"This is the deepfake defense. The signer proves they are physically present — not a photo or pre-recorded video."</div>
      <div class="note-deep">For ABS reps: This defeats photo spoofing attacks. The signer must move in a way that cannot be replicated with a still image. For Pem: "No other e-sign platform at this table does this."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(15)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(17)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 17 — Persona: Face Scan  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-17">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(7)}
          <div class="persona-step-label">Identity Verification · Step 8 of 9</div>
          <div class="persona-title">Look slightly left</div>
          <div class="persona-subtitle">Slowly turn your head left and right as indicated. Keep your face within the oval.</div>
          <div class="persona-camera-box">
            <div class="persona-face-oval">
              <div class="persona-face-icon">&#x1F9D1;</div>
            </div>
            <div class="persona-camera-hint">&#x2190; Turn slowly left &nbsp;&nbsp; Turn slowly right &#x2192;</div>
          </div>
          <div style="text-align:center;margin-top:12px;">
            <div style="display:inline-flex;align-items:center;gap:8px;background:#f0f7eb;border:1px solid var(--green);border-radius:20px;padding:6px 14px;">
              <div style="width:8px;height:8px;background:var(--green);border-radius:50%;animation:none;"></div>
              <span style="font-size:12px;font-weight:700;color:var(--green2);">Liveness check in progress...</span>
            </div>
          </div>
          <button class="btn-persona-primary" style="margin-top:16px;" onclick="goTo(18)">&#10003; Check Complete</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-17">
      <div class="notes-title">Speaker Notes — Screen 17: Face Scan [Full Flow]</div>
      <div class="note-main">"The signer's live face is compared against their ID photo. If they don't match, signing stops."</div>
      <div class="note-deep">For ABS reps: This is the biometric match — comparing facial geometry, not just visual similarity. For Aspen: "This makes the signature legally defensible. You can prove the person who signed is the person on the ID."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(16)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(18)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 18 — Persona: Verification Complete  [Full Flow]
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-18">
    <div class="persona-shell">
      <div class="persona-card">
        <div class="persona-card-header">
          <span class="persona-brand">Persona</span>
          <span class="persona-secure">&#128274; Encrypted &amp; Secure</span>
        </div>
        <div class="persona-card-body">
          {pdots(8)}
          <div class="persona-step-label">Identity Verification · Step 9 of 9</div>
          <div class="persona-success-icon">&#9989;</div>
          <div class="persona-title" style="text-align:center;">Congratulations, you're done!</div>
          <div class="persona-subtitle" style="text-align:center;">Your identity has been verified. You will be returned to the document to complete your signature.</div>
          <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:12px 14px;margin-bottom:20px;font-size:12px;color:#166534;line-height:1.6;">
            &#10003; Government ID scanned and verified<br>
            &#10003; Barcode data matched<br>
            &#10003; Biometric liveness check passed<br>
            &#10003; Face match: confirmed
          </div>
          <button class="btn-persona-primary" onclick="goTo(19)">Return to Document &rarr;</button>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-18">
      <div class="notes-title">Speaker Notes — Screen 18: Persona Complete [Full Flow]</div>
      <div class="note-main">"Verification passed. The result is written into the PKI-signed audit trail. The signer now proceeds to sign the document."</div>
      <div class="note-deep">For ABS reps: At this point, SIGNiX has confirmed the signer's identity. Everything from here is cryptographically tied to a verified person.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(17)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(19)">Next &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 19 — SIGNiX: ID Passed
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-19">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content">
      <div class="signix-result-wrap">
        <div class="signix-result-icon">&#9989;</div>
        <div class="signix-result-title">Congratulations!</div>
        <div class="signix-result-badge">&#128274; ID Verify — Passed</div>
        <div class="signix-result-sub">Your ID documents passed verification. The result has been recorded in your transaction's secure audit trail. Click Next to review and sign your document.</div>
        <div style="background:#f0f7eb;border:1px solid var(--green);border-radius:8px;padding:14px 18px;text-align:left;margin-bottom:28px;">
          <div style="font-size:12px;font-weight:700;color:var(--green2);margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;">What was verified:</div>
          <div style="font-size:13px;color:var(--body);line-height:1.7;">
            &#10003; Government-issued ID analyzed — credential analysis passed<br>
            &#10003; Barcode data cross-referenced with ID front — match confirmed<br>
            &#10003; Biometric liveness check — physically present<br>
            &#10003; Face match to ID photo — confirmed<br>
            &#10003; Verification result embedded in PKI-signed audit trail
          </div>
        </div>
        <button class="btn-verify" onclick="goTo(20)">Continue to Sign &rarr;</button>
      </div>
    </div>
    <div class="notes-panel" id="notes-19">
      <div class="notes-title">Speaker Notes — Screen 19: ID Passed</div>
      <div class="note-main">"SIGNiX confirms the identity check passed. This confirmation is part of the permanent audit trail."</div>
      <div class="note-deep">For Aspen: If a signer ever disputes the transaction, this record exists — timestamped, cryptographically locked. For ABS reps: Your customer can point to this screen as the moment identity was verified.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goBackFrom19()">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(20)">Create Signature &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 20 — Create Your Signature
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-20">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content">
      <div class="create-sig-card">
        <div style="font-size:20px;font-weight:800;color:var(--ink);margin-bottom:6px;"><span id="create-sig-name">Jane</span>, let's create your signature</div>
        <div style="font-size:13px;color:var(--muted);margin-bottom:24px;">Create a password to protect your signature. You'll use this password every time you sign with SIGNiX.</div>
        <div class="auth-input-group">
          <label>Create a Password</label>
          <input type="password" placeholder="Minimum 8 characters" value="••••••••••" />
        </div>
        <div class="auth-input-group">
          <label>Confirm Password</label>
          <input type="password" placeholder="Re-enter password" value="••••••••••" />
        </div>
        <div style="font-size:13px;font-weight:600;color:var(--ink);margin-bottom:12px;margin-top:4px;">Choose your signature style</div>
        <div class="sig-style-grid">
          <div class="sig-style-opt selected">
            <div class="sig-preview" id="sig-style-preview-1">Jane Smith</div>
            <div class="sig-style-name">Classic Cursive</div>
          </div>
          <div class="sig-style-opt">
            <div class="sig-preview" style="font-family:'Courier New',monospace;font-style:normal;font-size:18px;" id="sig-style-preview-2">Jane Smith</div>
            <div class="sig-style-name">Simple Print</div>
          </div>
          <div class="sig-style-opt">
            <div class="sig-preview" style="font-size:22px;" id="sig-style-preview-3">Jane Smith</div>
            <div class="sig-style-name">Elegant Script</div>
          </div>
          <div class="sig-style-opt">
            <div class="sig-preview" style="font-family:Arial,sans-serif;font-style:normal;font-weight:700;font-size:18px;" id="sig-style-preview-4">Jane Smith</div>
            <div class="sig-style-name">Bold Block</div>
          </div>
        </div>
        <button class="btn-verify" style="margin-top:8px;" onclick="goTo(21)">Save My Signature &amp; Proceed</button>
      </div>
    </div>
    <div class="notes-panel" id="notes-20">
      <div class="notes-title">Speaker Notes — Screen 20: Create Your Signature</div>
      <div class="note-main">"The signer creates a password that protects their electronic signature, then selects a style."</div>
      <div class="note-deep">For Aspen: The password is tied to the signer's PKI certificate — not a platform login. That's what makes the SIGNiX signature different from DocuSign's click-to-sign. For ABS reps: First-time signers create this once. Returning signers use their existing password.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(19)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(21)">Review Document &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 21 — Document View
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-21">
    <div class="signix-bar">
      <div class="signix-logo">SIGN<span>iX</span></div>
      <div style="display:flex;gap:6px;align-items:center;">
        <button class="btn-sm btn-outline-green btn-inert" style="font-size:11px;">&#x2193;</button>
        <button class="btn-sm btn-outline-green btn-inert" style="font-size:11px;">&#x1F5A8;</button>
        <button class="btn-logout">Logout</button>
      </div>
    </div>
    <div class="content" style="padding:0;">
      <div style="padding:10px 20px;background:var(--canvas);border-bottom:1px solid var(--rule);">
        <div class="progress-bar-wrap">
          <span class="progress-label">My Progress</span>
          <div class="progress-track"><div class="progress-fill" style="width:60%;"></div></div>
          <span style="font-size:12px;color:var(--muted);">60%</span>
        </div>
        <div style="font-size:11px;color:var(--muted);text-align:center;">County_Vendor_Services_Agreement_2026.pdf</div>
      </div>
      <div style="padding:20px;">
        <div class="signing-wrap">
          <div style="background:var(--white);border:1px solid var(--rule);border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,.1);">
            <div style="font-size:17px;font-weight:700;color:var(--ink);margin-bottom:10px;">Ready To Review and Sign?</div>
            <div style="font-size:13px;color:var(--body);line-height:1.6;margin-bottom:16px;">Select <strong>Go</strong> to jump right to your first action. Or choose <strong>Let Me Review</strong> to go at your own pace.</div>
            <div style="display:flex;justify-content:flex-end;gap:10px;">
              <button class="btn-sm btn-outline-green btn-inert" style="padding:8px 16px;font-size:13px;">Let Me Review</button>
              <button class="btn-sm btn-green" style="padding:8px 16px;font-size:13px;" onclick="goTo(22)">Go!</button>
            </div>
          </div>
          <div class="doc-header">
            <div style="font-size:14px;font-weight:900;color:var(--blue);">Los Angeles County</div>
            <div class="doc-title-line">VENDOR SERVICES AGREEMENT — 2026</div>
          </div>
          <div class="required-field">
            <span class="required-label">Required</span>
            <span style="font-size:13px;color:var(--body);">I, </span>
            <input class="required-input" id="doc-name-field" value="" placeholder="Your name" />
            <span style="font-size:13px;color:var(--body);">, agree to the terms of this agreement.</span>
          </div>
          <div class="doc-body-text">
            <ol>
              <li>The Vendor agrees to provide services as described in Exhibit A, incorporated herein by reference.</li>
              <li>All services shall be performed in compliance with applicable federal, state, and local laws, including the California Public Records Act.</li>
              <li>The County reserves the right to audit all records related to services performed under this agreement upon reasonable notice.</li>
              <li>This agreement is subject to the approval of the County's Board of Supervisors.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-21">
      <div class="notes-title">Speaker Notes — Screen 21: Document View</div>
      <div class="note-main">"The signer sees the document. Required fields are in yellow — they can't miss them. The system guides them straight to what needs to be done."</div>
      <div class="note-deep">For Aspen: The name field is pre-filled from the verified identity. For Pem: "Every required field is tracked. You can't finalize with something missing."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(20)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(22)">Place Signature &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 22 — Signature Placed
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-22">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content" style="padding:0;">
      <div style="padding:10px 20px;background:var(--canvas);border-bottom:1px solid var(--rule);">
        <div class="progress-bar-wrap">
          <span class="progress-label">My Progress</span>
          <div class="progress-track"><div class="progress-fill" style="width:95%;"></div></div>
          <span style="font-size:12px;color:var(--muted);">95%</span>
        </div>
      </div>
      <div style="padding:20px;">
        <div style="background:var(--white);border:1px solid var(--rule);border-radius:8px;padding:24px;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,.1);max-width:480px;margin-left:auto;margin-right:auto;">
          <div class="finish-title">Finished Signing?</div>
          <div class="finish-text">Almost done! Tap <strong>Finish</strong> to confirm your signatures. Or select <strong>Stay Here</strong> to keep reviewing.</div>
          <div class="finish-btns">
            <button class="btn-sm btn-outline-green btn-inert" style="padding:10px 20px;">Stay Here</button>
            <button class="btn-sm btn-green" style="padding:10px 20px;" onclick="goTo(23)">Finish</button>
          </div>
        </div>
        <div class="signing-wrap">
          <div class="doc-header">
            <div style="font-size:14px;font-weight:900;color:var(--blue);">Los Angeles County</div>
            <div class="doc-title-line">VENDOR SERVICES AGREEMENT — 2026</div>
          </div>
          <div class="doc-body-text" style="margin-bottom:16px;"><em>By signing below, I confirm that I have read, understand, and agree to each of the terms stated herein.</em></div>
          <div class="sig-block">
            <div class="sig-row">
              <div>
                <div class="sig-field"><label>Employee Signature <span class="sig-badge">Image</span></label></div>
                <div class="sig-line signed" id="sig-display-name" style="font-size:18px;">Jane Smith</div>
              </div>
              <div></div>
              <div>
                <div class="sig-field"><label>Signed Date</label></div>
                <div class="sig-line" id="sig-date"></div>
              </div>
            </div>
            <div>
              <div class="sig-field"><label>Printed Name</label></div>
              <div class="name-field" id="sig-printed-name">Jane Smith</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-22">
      <div class="notes-title">Speaker Notes — Screen 22: Signature Placed</div>
      <div class="note-main">"Signature is placed. The document is locked the moment they click Finish. Nothing can be altered after this point."</div>
      <div class="note-deep">For Aspen: The signature is PKI-embedded — not an image of a name. It is cryptographically tied to the document. One character change and the signature is invalidated. For Pem: "This is the difference between a signature that looks right and one that holds up."</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(21)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="goTo(23)">Finish &rarr;</button>
    </div>
  </div>

  <!-- ══════════════════════════════════════════════════════
       SCREEN 23 — Confirmation + QR Code
  ══════════════════════════════════════════════════════════ -->
  <div class="screen" id="screen-23">
    <div class="signix-bar"><div class="signix-logo">SIGN<span>iX</span></div><button class="btn-logout">Logout</button></div>
    <div class="content">
      <div class="confirm-wrap">
        <div style="font-size:48px;margin-bottom:12px;">&#10003;</div>
        <div class="confirm-title"><span id="confirm-name">Jane</span>, thanks for signing online!</div>
        <div class="confirm-text">You have successfully completed all required actions.</div>
        <div class="confirm-grid">
          <div>
            <div style="padding:16px;background:#f0f7eb;border:1px solid var(--green);border-radius:8px;margin-bottom:16px;">
              <div style="font-size:12px;font-weight:700;color:var(--green2);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">What happens next</div>
              <div style="font-size:13px;color:var(--body);line-height:1.7;">
                &#x2022; The document is PKI-signed and cryptographically locked.<br>
                &#x2022; A full audit trail has been recorded: who signed, when, and how they authenticated.<br>
                &#x2022; The signed document is stored securely and available for download or records request.<br>
                &#x2022; <strong>You own and control your documents.</strong>
              </div>
            </div>
            <div style="display:flex;gap:12px;">
              <button class="btn-sm btn-outline-green btn-inert" style="padding:10px 20px;">Review Document</button>
              <button class="btn-sm btn-green" style="padding:10px 20px;" onclick="resetDemo()">&#8635; New Demo</button>
            </div>
          </div>
          {QR_BLOCK}
        </div>
      </div>
    </div>
    <div class="notes-panel" id="notes-23">
      <div class="notes-title">Speaker Notes — Screen 23: Confirmation</div>
      <div class="note-main">"Done. Signed, locked, stored. You own it. Full audit trail proving who signed, when, and how they authenticated."</div>
      <div class="note-deep">For Aspen: Pause here. Let "You own and control your documents" land. Then ask: "What would it mean for your county if you had this level of proof on every signed document?" For ABS reps: Invite the prospect to scan the QR code to book time with Aspen directly.</div>
    </div>
    <div class="nav-bar">
      <button class="btn-nav btn-back" onclick="goTo(22)">&larr; Back</button>
      <button class="btn-nav btn-next" onclick="resetDemo()">&#8635; Start New Demo</button>
    </div>
  </div>

</div><!-- /demo-shell -->

<script>
  var currentScreen = 1;
  var notesVisible  = false;
  var fullFlow      = false;
  var signerFirst   = 'Jane';
  var signerLast    = 'Smith';
  var signerEmail   = 'jane.smith@lacounty.gov';
  var authMethod    = 'ID Verify';

  var QUICK_SCREENS = [1,2,3,4,5,6,7,8,9,19,20,21,22,23];
  var FULL_SCREENS  = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
  var ALL_SCREENS   = 23;

  function getScreenList() {{ return fullFlow ? FULL_SCREENS : QUICK_SCREENS; }}
  function getDisplayStep(id) {{
    var list = getScreenList();
    var idx  = list.indexOf(id);
    return idx === -1 ? 1 : idx + 1;
  }}
  function getTotalSteps() {{ return getScreenList().length; }}

  function goTo(n) {{
    if (!fullFlow && n >= 10 && n <= 18) n = 19;
    document.getElementById('screen-' + currentScreen).classList.remove('active');
    currentScreen = n;
    document.getElementById('screen-' + currentScreen).classList.add('active');
    document.getElementById('step-counter').textContent =
      'Step ' + getDisplayStep(n) + ' of ' + getTotalSteps();

    var full  = (signerFirst + ' ' + signerLast).trim() || 'Jane Smith';
    var first = signerFirst || 'Jane';
    function setEl(id, v)  {{ var e = document.getElementById(id); if (e) e.textContent = v; }}
    function setVal(id, v) {{ var e = document.getElementById(id); if (e) e.value = v; }}
    setEl('signer-display-name', full);
    setEl('signer-display-email', signerEmail);
    setEl('signer-display-auth', authMethod);
    setEl('email-to-name', full);
    setEl('email-greeting-name', first);
    setEl('consent-name', full);
    setEl('auth-name', first);
    setEl('confirm-name', first);
    setEl('create-sig-name', first);
    setEl('sig-display-name', full);
    setEl('sig-printed-name', full);
    setVal('doc-name-field', full);
    ['sig-style-preview-1','sig-style-preview-2','sig-style-preview-3','sig-style-preview-4'].forEach(function(id) {{ setEl(id, full); }});
    var today = new Date().toLocaleDateString('en-US', {{month:'short',day:'numeric',year:'numeric'}});
    setEl('sig-date', today);
    updateNotesPanel();
    window.scrollTo(0, 0);
  }}

  function goBackFrom19() {{ goTo(fullFlow ? 18 : 9); }}
  function goToAfterIDVerify() {{ goTo(fullFlow ? 10 : 19); }}

  function toggleFlow() {{
    fullFlow = !fullFlow;
    var btn = document.getElementById('btn-flow');
    btn.classList.toggle('active', fullFlow);
    btn.textContent = fullFlow ? 'Full Flow ON' : 'Full Flow';
    document.getElementById('step-counter').textContent =
      'Step ' + getDisplayStep(currentScreen) + ' of ' + getTotalSteps();
  }}

  function iAmTheSigner(checked) {{
    var f = document.getElementById('signer-first');
    var l = document.getElementById('signer-last');
    var e = document.getElementById('signer-email');
    var a = document.getElementById('auth-select');
    if (checked) {{
      f.value = 'Aspen'; l.value = 'Arias'; e.value = 'aarias@signix.com';
      a.value = 'idverify'; handleAuthChange();
    }} else {{
      f.value = ''; l.value = ''; e.value = ''; a.value = '';
      document.getElementById('auth-badge').classList.remove('visible');
      authMethod = 'ID Verify';
    }}
    updateSignerName();
  }}

  function updateSignerName() {{
    signerFirst = document.getElementById('signer-first').value.trim();
    signerLast  = document.getElementById('signer-last').value.trim();
    signerEmail = document.getElementById('signer-email').value.trim() || 'jane.smith@lacounty.gov';
  }}

  function handleAuthChange() {{
    var sel   = document.getElementById('auth-select');
    var badge = document.getElementById('auth-badge');
    if (sel.value === 'idverify') {{
      badge.classList.add('visible'); authMethod = 'ID Verify';
    }} else if (sel.value === 'kba') {{
      badge.classList.remove('visible'); authMethod = 'KBA-ID';
    }} else if (sel.value === '2fa') {{
      badge.classList.remove('visible'); authMethod = '2FA (SMS)';
    }} else {{
      badge.classList.remove('visible');
      authMethod = sel.options[sel.selectedIndex].text || 'Password';
    }}
    updateSignerName();
  }}

  function addSigner() {{
    updateSignerName();
    if (!document.getElementById('signer-first').value.trim()) {{
      document.getElementById('signer-first').value = 'Jane'; signerFirst = 'Jane';
    }}
    if (!document.getElementById('signer-last').value.trim()) {{
      document.getElementById('signer-last').value = 'Smith'; signerLast = 'Smith';
    }}
    if (!document.getElementById('auth-select').value) {{
      document.getElementById('auth-select').value = 'idverify'; handleAuthChange();
    }}
  }}

  function addSignerAndAdvance() {{ addSigner(); goTo(3); }}

  function toggleNotes() {{ notesVisible = !notesVisible; updateNotesPanel(); }}

  function updateNotesPanel() {{
    for (var i = 1; i <= ALL_SCREENS; i++) {{
      var p = document.getElementById('notes-' + i);
      if (p) p.classList.toggle('visible', notesVisible && i === currentScreen);
    }}
  }}

  function resetDemo() {{
    signerFirst = 'Jane'; signerLast = 'Smith';
    signerEmail = 'jane.smith@lacounty.gov'; authMethod = 'ID Verify';
    ['signer-first','signer-last','signer-email','auth-select'].forEach(function(id) {{
      var el = document.getElementById(id); if (el) el.value = '';
    }});
    var b = document.getElementById('auth-badge'); if (b) b.classList.remove('visible');
    document.querySelectorAll('.demo-shell input[type="checkbox"]').forEach(function(cb) {{ cb.checked = false; }});
    document.querySelectorAll('.demo-shell input[type="radio"]').forEach(function(rb) {{ rb.checked = false; }});
    var demoYes = document.querySelector('input[name="demo"]');
    var consent  = document.querySelector('input[name="consent"]');
    if (demoYes) demoYes.checked = true;
    if (consent)  consent.checked = true;
    fullFlow = false;
    var btn = document.getElementById('btn-flow'); btn.classList.remove('active'); btn.textContent = 'Full Flow';
    goTo(1);
  }}
</script>

</body>
</html>"""

OUT = os.path.join(OUTPUT_DIR, "SIGNiX_MyDox_Demo.html")
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(HTML)
print(f"Written: {OUT}")
print("Done.")
