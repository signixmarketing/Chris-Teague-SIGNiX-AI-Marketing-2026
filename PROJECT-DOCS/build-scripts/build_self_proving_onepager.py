#!/usr/bin/env python3
"""
Build SIGNiX Self-Proving Signatures One-Pager — Aspen Arias contact version.

Core argument: SIGNiX-signed documents are self-proving. If SIGNiX ceased to
exist tomorrow, every document signed through SIGNiX still proves itself in
court, in an audit, or in a records request. DocuSign-signed documents require
DocuSign's continued cooperation to present as full evidence.

Visual centerpiece: side-by-side document inspection results (recreated from
the PDF Signature Inspector analysis of real signed documents).

Run from any directory:
  python3 "PROJECT-DOCS/build-scripts/build_self_proving_onepager.py"

Output:
  PROJECT-DOCS/DELIVERABLES/SIGNiX-SelfProving-OnePager-Aspen.html
  PROJECT-DOCS/DELIVERABLES/SIGNiX-SelfProving-OnePager-Aspen.pdf
"""

import os
import subprocess

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DELIVERABLES"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ASPEN_PHONE    = "(423) 635-7112"
ASPEN_EMAIL    = "aarias@signix.com"
ASPEN_CALENDAR = "https://www.signix.com/meetings/aarias5?uuid=83e31d03-9c7e-41ec-b8a0-feb138363f27"
ASPEN_PHOTO    = "aspen-contact.png"

LOGO_URL = ("https://www.signix.com/hs-fs/hubfs/"
            "SIGNiX%20Logo%20Main-Jan-05-2023-02-38-25-2345-AM-1.png?width=200")

CSS = """
    @page { size: Letter; margin: 0; }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --green:       #6da34a;
      --green2:      #5a8c3b;
      --ink:         #2e3440;
      --body:        #545454;
      --muted:       #6b7280;
      --white:       #ffffff;
      --canvas:      #f8fafb;
      --rule:        #d8dee9;
      --green-light: #f0f7eb;
      --amber:       #d97706;
      --amber-light: #fffbeb;
      --red:         #dc2626;
      --red-light:   #fef2f2;
    }
    html, body {
      width: 8.5in; height: 11in;
      font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
      color: var(--body); background: var(--white);
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    .page { width: 8.5in; height: 11in; display: flex; flex-direction: column; overflow: hidden; }

    /* ── HEADER ── */
    .header { background-color: var(--ink); padding: 0.32in 0.5in 0.28in; flex-shrink: 0; }
    .header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.18in; }
    .logo img { height: 32pt; width: auto; display: block; }
    .header-eyebrow { font-size: 7.5pt; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--green); margin-bottom: 0.07in; }
    .header-headline { font-size: 24pt; font-weight: 800; color: var(--white); line-height: 1.15; letter-spacing: -0.01em; margin-bottom: 0.09in; }
    .header-headline span { color: var(--green); }
    .header-rule { width: 0.4in; height: 3pt; background: var(--green); border-radius: 2pt; margin-bottom: 0.09in; }
    .header-sub { font-size: 9.5pt; color: rgba(255,255,255,0.72); line-height: 1.45; max-width: 6in; }
    .header-sub strong { color: var(--white); }

    /* ── BODY ── */
    .body { flex: 1; display: flex; flex-direction: column; padding: 0.22in 0.5in 0.18in; gap: 0.16in; }

    /* ── SECTION LABEL ── */
    .section-label { font-size: 7pt; font-weight: 700; letter-spacing: 0.13em; text-transform: uppercase; color: var(--green); margin-bottom: 0.08in; }

    /* ── SIDE-BY-SIDE PANELS ── */
    .compare-grid { display: flex; gap: 0.18in; flex-shrink: 0; }

    .doc-panel { flex: 1; border-radius: 6pt; overflow: hidden; border: 1.5pt solid var(--rule); }

    .panel-header {
      padding: 0.1in 0.14in 0.09in;
      display: flex; flex-direction: column; gap: 3pt;
    }
    .panel-header.signix  { background: var(--ink); border-bottom: 2pt solid var(--green); }
    .panel-header.docusign { background: #eceff4; border-bottom: 2pt solid var(--rule); }

    .panel-platform { font-size: 8.5pt; font-weight: 800; letter-spacing: 0.04em; }
    .panel-platform.signix  { color: var(--green); }
    .panel-platform.docusign { color: var(--muted); }

    .panel-cert { font-size: 7.5pt; font-weight: 600; }
    .panel-cert.signix  { color: rgba(255,255,255,0.75); }
    .panel-cert.docusign { color: var(--body); }

    .panel-cert-owner { font-size: 7pt; }
    .panel-cert-owner.signix  { color: rgba(255,255,255,0.5); }
    .panel-cert-owner.docusign { color: var(--muted); }

    .panel-rows { padding: 0; }
    .panel-row {
      display: flex; align-items: center; justify-content: space-between;
      padding: 5pt 10pt; border-bottom: 1pt solid var(--rule); gap: 8pt;
    }
    .panel-row:last-child { border-bottom: none; }
    .panel-row:nth-child(even) { background: var(--canvas); }

    .row-label { font-size: 7.5pt; color: var(--muted); font-weight: 600; flex: 1; }
    .row-val   { font-size: 7.5pt; font-weight: 700; text-align: right; white-space: nowrap; }
    .row-val.yes  { color: var(--green); }
    .row-val.no   { color: var(--red); }
    .row-val.neutral { color: var(--body); }

    .check { color: var(--green); font-size: 9pt; margin-right: 2pt; }
    .cross { color: var(--red);   font-size: 9pt; margin-right: 2pt; }

    /* ── VERDICT ROW ── */
    .verdict-row {
      padding: 7pt 10pt;
      font-size: 8pt; font-weight: 700; text-align: center;
      border-top: 2pt solid;
    }
    .verdict-row.signix  { background: var(--green-light); color: var(--green2); border-color: var(--green); }
    .verdict-row.docusign { background: var(--red-light);  color: var(--red);    border-color: #fca5a5; }

    /* ── DEPENDENCY STRIP ── */
    .dependency-strip {
      background: var(--ink); border-radius: 5pt;
      padding: 0.13in 0.18in; flex-shrink: 0;
      display: grid; grid-template-columns: 1fr 1fr; gap: 0.18in; align-items: start;
    }
    .dep-scenario { }
    .dep-label { font-size: 7pt; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--green); margin-bottom: 5pt; }
    .dep-q { font-size: 9pt; font-weight: 700; color: var(--white); line-height: 1.5; font-style: italic; margin-bottom: 6pt; }
    .dep-answers { display: flex; flex-direction: column; gap: 4pt; }
    .dep-answer { font-size: 8pt; line-height: 1.45; padding: 4pt 8pt; border-radius: 3pt; }
    .dep-answer.yes { background: var(--green-light); color: var(--green2); }
    .dep-answer.no  { background: var(--red-light); color: var(--red); }
    .dep-platform { font-weight: 800; }
    .dep-right-label { font-size: 7pt; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--green); margin-bottom: 5pt; }
    .dep-right-text { font-size: 8.5pt; color: rgba(255,255,255,0.8); line-height: 1.6; }
    .dep-right-text strong { color: var(--white); }

    /* ── CONTACT ── */
    .contact { background: var(--canvas); border: 1pt solid var(--rule); border-radius: 5pt; padding: 0.1in 0.18in; display: flex; align-items: center; gap: 0.15in; flex-shrink: 0; }
    .contact-photo { width: 44pt; height: 44pt; border-radius: 50%; object-fit: cover; flex-shrink: 0; border: 2pt solid var(--green); }
    .contact-info { flex: 1; }
    .contact-name  { font-size: 10pt; font-weight: 800; color: var(--ink); line-height: 1.2; }
    .contact-title { font-size: 7.5pt; color: var(--muted); margin-bottom: 3pt; }
    .contact-details { font-size: 7.5pt; color: var(--body); line-height: 1.6; }
    .contact-details a { color: var(--green); text-decoration: none; font-weight: 600; }
    .contact-right { text-align: right; flex-shrink: 0; }
    .contact-cta  { font-size: 7pt; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3pt; }
    .contact-url a { font-size: 8.5pt; font-weight: 800; color: var(--green); text-decoration: none; }

    /* ── FOOTER ── */
    .footer { padding: 0.07in 0.5in; border-top: 1pt solid var(--rule); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
    .footer-left  { font-size: 6.5pt; color: var(--muted); }
    .footer-right { font-size: 6.5pt; color: var(--muted); }
"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SIGNiX — Your Signature Proves Itself</title>
  <style>
{CSS}
  </style>
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <div class="header">
    <div class="header-top">
      <div class="logo"><img src="{LOGO_URL}" alt="SIGNiX" /></div>
    </div>
    <div class="header-eyebrow">Signature authentication &amp; document independence</div>
    <div class="header-headline">Your signature proves itself.<br /><span>No platform required.</span></div>
    <div class="header-rule"></div>
    <div class="header-sub">
      If your e-signature vendor went away tomorrow, could you still prove your documents are authentic?
      With SIGNiX, <strong>yes</strong>. The evidence is inside the file.
      With most platforms, the answer depends on their continued cooperation.
    </div>
  </div>

  <!-- BODY -->
  <div class="body">

    <!-- SECTION LABEL -->
    <div class="section-label">What a signed document actually contains &mdash; a direct comparison</div>

    <!-- SIDE-BY-SIDE DOCUMENT PANELS -->
    <div class="compare-grid">

      <!-- SIGNIX PANEL -->
      <div class="doc-panel">
        <div class="panel-header signix">
          <div class="panel-platform signix">&#x2713;&nbsp; SIGNiX</div>
          <div class="panel-cert signix">GlobalSign AATL &mdash; Signer-Level Certificate</div>
          <div class="panel-cert-owner signix">Certificate belongs to: SIGNiX Signature Authority on behalf of the signer</div>
        </div>
        <div class="panel-rows">
          <div class="panel-row">
            <span class="row-label">PKI signature on document</span>
            <span class="row-val yes"><span class="check">&#10003;</span>GlobalSign AATL</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Tamper detection (ByteRange)</span>
            <span class="row-val yes"><span class="check">&#10003;</span>100% of file covered</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Signer IP address in PDF</span>
            <span class="row-val yes"><span class="check">&#10003;</span>Embedded in document</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Signer device in PDF</span>
            <span class="row-val yes"><span class="check">&#10003;</span>Embedded in document</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Transaction ID in PDF</span>
            <span class="row-val yes"><span class="check">&#10003;</span>Embedded in document</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Authentication method in file</span>
            <span class="row-val yes"><span class="check">&#10003;</span>OTP / ID Verify / KBA</span>
          </div>
          <div class="panel-row">
            <span class="row-label">PKI-signed audit trail</span>
            <span class="row-val yes"><span class="check">&#10003;</span>2 PKI sigs &middot; GlobalSign chain</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Audit trail tamper protection</span>
            <span class="row-val yes"><span class="check">&#10003;</span>ByteRange-protected</span>
          </div>
        </div>
        <div class="verdict-row signix">Document is self-proving &mdash; open in any PDF reader to verify</div>
      </div>

      <!-- DOCUSIGN PANEL -->
      <div class="doc-panel">
        <div class="panel-header docusign">
          <div class="panel-platform docusign">DocuSign (standard)</div>
          <div class="panel-cert docusign">DigiCert AATL &mdash; Server Export Certificate</div>
          <div class="panel-cert-owner docusign">Certificate belongs to: DS Technical Operations (DocuSign server)</div>
        </div>
        <div class="panel-rows">
          <div class="panel-row">
            <span class="row-label">PKI signature on document</span>
            <span class="row-val neutral"><span class="check" style="color:var(--body);">&#10003;</span>DigiCert AATL</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Tamper detection (ByteRange)</span>
            <span class="row-val neutral"><span class="check" style="color:var(--body);">&#10003;</span>ByteRange hash</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Signer IP address in PDF</span>
            <span class="row-val no"><span class="cross">&#10007;</span>Cloud only &mdash; requires DocuSign</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Signer device in PDF</span>
            <span class="row-val no"><span class="cross">&#10007;</span>Cloud only &mdash; requires DocuSign</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Transaction ID in PDF</span>
            <span class="row-val no"><span class="cross">&#10007;</span>Cloud only &mdash; requires DocuSign</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Authentication method in file</span>
            <span class="row-val no"><span class="cross">&#10007;</span>Cloud audit log only</span>
          </div>
          <div class="panel-row">
            <span class="row-label">PKI-signed audit trail</span>
            <span class="row-val no"><span class="cross">&#10007;</span>Standard PDF &middot; 0 PKI sigs</span>
          </div>
          <div class="panel-row">
            <span class="row-label">Audit trail tamper protection</span>
            <span class="row-val no"><span class="cross">&#10007;</span>No ByteRange protection</span>
          </div>
        </div>
        <div class="verdict-row docusign">Proof requires DocuSign&rsquo;s cooperation &mdash; platform dependency</div>
      </div>

    </div>

    <!-- DEPENDENCY STRIP -->
    <div class="dependency-strip">
      <div class="dep-scenario">
        <div class="dep-label">The question in any dispute, audit, or records request</div>
        <div class="dep-q">&ldquo;Can you prove who signed this document without calling your e-signature vendor?&rdquo;</div>
        <div class="dep-answers">
          <div class="dep-answer yes"><span class="dep-platform">SIGNiX:</span> Yes. Open the PDF. The signer&rsquo;s certificate, IP, device, and authentication method are in the file.</div>
          <div class="dep-answer no"><span class="dep-platform">Standard platforms:</span> The certificate belongs to the vendor&rsquo;s server. Signer identity lives in their cloud. Full proof requires their records.</div>
        </div>
      </div>
      <div class="dep-right">
        <div class="dep-right-label">What vendor dependency means long-term</div>
        <div class="dep-right-text">
          If your e-signature vendor raises prices, gets acquired, or goes out of business,
          <strong>your signed SIGNiX documents remain fully provable.</strong>
          The evidence is inside each file, anchored to a public GlobalSign certificate chain
          that any court, auditor, or records officer can verify independently.
          No vendor cooperation. No service dependency. No risk.
        </div>
      </div>
    </div>

    <!-- CONTACT BLOCK -->
    <div class="contact">
      <img class="contact-photo" src="{ASPEN_PHOTO}" alt="Aspen Arias" />
      <div class="contact-info">
        <div class="contact-name">Aspen Arias</div>
        <div class="contact-title">Account Executive, SIGNiX</div>
        <div class="contact-details">
          {ASPEN_PHONE} &nbsp;&nbsp;|&nbsp;&nbsp;
          <a href="mailto:{ASPEN_EMAIL}">{ASPEN_EMAIL}</a>
        </div>
      </div>
      <div class="contact-right">
        <div class="contact-cta">Book a meeting</div>
        <div class="contact-url">
          <a href="{ASPEN_CALENDAR}">signix.com/meetings/aarias5</a>
        </div>
      </div>
    </div>

  </div>
  <!-- /BODY -->

  <!-- FOOTER -->
  <div class="footer">
    <div class="footer-left">SIGNiX &middot; 1110 Market St, Suite 400, Chattanooga, TN 37402 &middot; signix.com</div>
    <div class="footer-right">Comparison based on PKI inspection of real signed documents. Certificate data extracted from production PDFs.</div>
  </div>

</div>
</body>
</html>"""

# ── Write HTML ────────────────────────────────────────────────────────────────
html_filename = "SIGNiX-SelfProving-OnePager-Aspen.html"
pdf_filename  = "SIGNiX-SelfProving-OnePager-Aspen.pdf"
html_path = os.path.join(OUTPUT_DIR, html_filename)
pdf_path  = os.path.join(OUTPUT_DIR, pdf_filename)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"  Written: {html_filename}")

# ── Generate PDF via Chrome headless ─────────────────────────────────────────
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

cmd = [
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    f"--print-to-pdf={pdf_path}",
    "--no-pdf-header-footer",
    f"file://{html_path}",
]
print(f"\n  Generating {pdf_filename} ...")
result = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(pdf_path):
    print(f"  PDF written: {pdf_path}")
else:
    print("  ERROR generating PDF:")
    print(result.stderr[-600:] if result.stderr else "(no stderr)")

print("\nDone.")
