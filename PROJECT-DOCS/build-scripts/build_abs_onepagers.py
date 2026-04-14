#!/usr/bin/env python3
"""
Build ABS CoPilot one-pagers — both versions, clean PDFs via Chrome headless.

What this script does:
  1. Reads the two ABS HTML source files from DELIVERABLES/.
  2. Removes the "Draft · Internal review only" label.
  3. Updates both CTAs with Aspen's real phone, email, and calendar link.
  4. Writes the updated HTML back to DELIVERABLES/.
  5. Generates PDFs using Chrome headless (full modern rendering).

Output:
  PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html  (updated)
  PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_OnePager_v2_aspen.pdf
  PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html  (updated)
  PROJECT-DOCS/DELIVERABLES/SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.pdf

Run from any directory:
  python3 "PROJECT-DOCS/build-scripts/build_abs_onepagers.py"
"""

import os
import subprocess

DELIVERABLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DELIVERABLES"
)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ASPEN_PHONE    = "(423) 635-7112"
ASPEN_EMAIL    = "aarias@signix.com"
ASPEN_CALENDAR = "https://www.signix.com/meetings/aarias5?uuid=83e31d03-9c7e-41ec-b8a0-feb138363f27"
ASPEN_CALENDAR_SHORT = "signix.com/meetings/aarias5"

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_html(filename):
    path = os.path.join(DELIVERABLES, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_html(filename, content):
    path = os.path.join(DELIVERABLES, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Updated: {filename}")

def generate_pdf(html_filename):
    pdf_filename = html_filename.replace(".html", ".pdf")
    html_path = os.path.join(DELIVERABLES, html_filename)
    pdf_path  = os.path.join(DELIVERABLES, pdf_filename)
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
        print(f"  ERROR generating PDF:")
        print(result.stderr[-600:] if result.stderr else "(no stderr)")


# ── File 1: CoPilot workflow overview ─────────────────────────────────────────

V2_FILE = "SIGNiX_ABS_CoPilot_OnePager_v2_aspen.html"

v2 = read_html(V2_FILE)

# Remove the "Draft · Internal review only" label
v2 = v2.replace(
    '<p class="cta-draft">Draft · Internal review only</p>',
    ""
)

# Replace the generic CTA copy and contact link with Aspen's real details
v2 = v2.replace(
    '<p class="cta-primary">Contact Aspen to learn more about SIGNiX.</p>',
    f"""<p class="cta-primary">Aspen Arias &mdash; Account Executive</p>
          <p class="cta-body">{ASPEN_PHONE} &nbsp;&nbsp;|&nbsp;&nbsp;
          <a href="mailto:{ASPEN_EMAIL}" style="color:#6da34a;font-weight:600;text-decoration:none;">{ASPEN_EMAIL}</a></p>"""
)

# Update QR code link and label from signix.com/contact to Aspen's calendar
v2 = v2.replace(
    'href="https://www.signix.com/contact" target="_blank" rel="noopener noreferrer" aria-label="Open SIGNiX contact form"',
    f'href="{ASPEN_CALENDAR}" target="_blank" rel="noopener noreferrer" aria-label="Book a meeting with Aspen"'
)
v2 = v2.replace(
    'href="https://www.signix.com/contact" target="_blank" rel="noopener noreferrer">signix.com/contact</a>',
    f'href="{ASPEN_CALENDAR}" target="_blank" rel="noopener noreferrer">{ASPEN_CALENDAR_SHORT}</a>'
)

write_html(V2_FILE, v2)
generate_pdf(V2_FILE)


# ── File 2: Authentication one-pager ──────────────────────────────────────────

AUTH_FILE = "SIGNiX_ABS_CoPilot_Authentication_OnePager_aspen.html"

auth = read_html(AUTH_FILE)

# Replace generic CTA copy with Aspen's real details
auth = auth.replace(
    '<p class="cta-primary">Contact Aspen to map the right authentication stack for your CoPilot workflows.</p>\n          <p class="cta-note">Scan to connect with SIGNiX and review ID Verify, KBA, and multi-layer authentication options.</p>',
    f"""<p class="cta-primary">Aspen Arias &mdash; Account Executive</p>
          <p class="cta-note">{ASPEN_PHONE} &nbsp;&nbsp;|&nbsp;&nbsp;
          <a href="mailto:{ASPEN_EMAIL}" style="color:#6da34a;font-weight:600;text-decoration:none;">{ASPEN_EMAIL}</a></p>
          <p class="cta-note" style="margin-top:0.18rem;">Scan to book a meeting and map the right authentication stack for your workflows.</p>"""
)

# Update QR code link and label from signix.com/contact to Aspen's calendar
auth = auth.replace(
    'href="https://www.signix.com/contact" target="_blank" rel="noopener noreferrer" aria-label="Open SIGNiX contact form"',
    f'href="{ASPEN_CALENDAR}" target="_blank" rel="noopener noreferrer" aria-label="Book a meeting with Aspen"'
)
auth = auth.replace(
    'href="https://www.signix.com/contact" target="_blank" rel="noopener noreferrer">signix.com/contact</a>',
    f'href="{ASPEN_CALENDAR}" target="_blank" rel="noopener noreferrer">{ASPEN_CALENDAR_SHORT}</a>'
)

write_html(AUTH_FILE, auth)
generate_pdf(AUTH_FILE)

print("\nDone. Both ABS one-pagers rebuilt with Chrome headless.")
