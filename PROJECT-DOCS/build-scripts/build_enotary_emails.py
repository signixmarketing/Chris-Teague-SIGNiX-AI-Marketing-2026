#!/usr/bin/env python3
"""
Build ACS eNotary Auto-Response Email Sequence — 4 emails.

Audience: Leads who inquire about SIGNiX's eNotary / RON platform.
Sender:   «REP_NAME» / «REP_TITLE» (replace before sending)
Output:   PROJECT-DOCS/DELIVERABLES/eNotary-Email-[1-4]-*.html

Run from any directory:
  python3 "PROJECT-DOCS/build-scripts/build_enotary_emails.py"
"""

import os, datetime

# ── Brand tokens ──────────────────────────────────────────────────────────────
GREEN  = "#6da34a"
INK    = "#2e3440"
BODY   = "#545454"
MUTED  = "#6b7280"
WHITE  = "#ffffff"
CANVAS = "#f8fafb"
RULE   = "#d8dee9"

LOGO = ("https://www.signix.com/hs-fs/hubfs/"
        "SIGNiX%20Logo%20Main-Jan-05-2023-02-38-25-2345-AM-1.png?width=200")

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DELIVERABLES"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

TODAY = datetime.date.today().strftime("%B %d, %Y")


# ── Shared shell ──────────────────────────────────────────────────────────────
def shell(tag_label, subject_a, subject_b, preview, body_html, cta_label,
          footer_note, filename):
    """Wrap body_html in the standard SIGNiX email shell."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{filename.replace("-", " ").replace(".html", "")}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <!--
    {filename}
    Series: ACS eNotary Auto-Response Sequence
    Subject line (A): {subject_a}
    Subject line (B): {subject_b}
    Preview text: {preview}

    Paste into HubSpot or Outlook:
    1) Open in Chrome or Edge.
    2) Replace all <<PLACEHOLDERS>> with real values.
    3) Replace [[REP_CALENDAR_LINK]] with the rep's calendar link.
    4) Select all (Cmd+A), copy, paste into email body.
    5) Send a test to yourself before deploying.

    Built: {TODAY}
  -->
</head>
<body style="margin:0;padding:0;background-color:{CANVAS};">

  <!-- Preheader -->
  <div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">
    {preview}
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background-color:{CANVAS};">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600"
               style="width:100%;max-width:600px;background-color:{WHITE};border:1px solid {RULE};border-radius:8px;overflow:hidden;">

          <!-- Logo -->
          <tr>
            <td style="padding:20px 28px 16px;border-bottom:3px solid {GREEN};">
              <a href="https://www.signix.com/" target="_blank" rel="noopener noreferrer"
                 style="text-decoration:none;">
                <img src="{LOGO}" width="200" height="59" alt="SIGNiX"
                     style="display:block;border:0;height:auto;max-width:200px;" />
              </a>
            </td>
          </tr>

          <!-- Tag + sender -->
          <tr>
            <td style="padding:24px 28px 10px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
              <p style="margin:0 0 14px;font-size:11px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{GREEN};">
                {tag_label}
              </p>
              <p style="margin:0 0 6px;font-size:14px;line-height:1.45;color:{BODY};">
                <strong style="color:{INK};"><<REP_NAME>></strong> &middot; <<REP_TITLE>>,
                <a href="https://www.signix.com/" target="_blank" rel="noopener noreferrer"
                   style="color:{GREEN};font-weight:600;text-decoration:none;">SIGNiX</a>
              </p>
              <p style="margin:0 0 18px;font-size:16px;line-height:1.55;color:{BODY};">
                Hi <<FIRST_NAME>>,
              </p>
{body_html}
            </td>
          </tr>

          <!-- CTA button -->
          <tr>
            <td align="center" style="padding:8px 28px 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="background-color:{GREEN};border-radius:6px;">
                    <a href="[[REP_CALENDAR_LINK]]" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;padding:14px 28px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:15px;font-weight:700;color:{WHITE};text-decoration:none;letter-spacing:0.01em;">
                      {cta_label}
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 28px;">
              <div style="border-top:1px solid {RULE};"></div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 28px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
              <p style="margin:0 0 6px;font-size:13px;color:{MUTED};">
                <<REP_NAME>> &middot; <<REP_TITLE>><br />
                <a href="mailto:<<REP_EMAIL>>" style="color:{GREEN};text-decoration:none;"><<REP_EMAIL>></a>
                &nbsp;&middot;&nbsp;
                <a href="tel:<<REP_PHONE>>" style="color:{GREEN};text-decoration:none;"><<REP_PHONE>></a>
              </p>
              <p style="margin:16px 0 0;font-size:11px;line-height:1.6;color:{MUTED};">
                {footer_note}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Written: {filename}")
    return path


# ── EMAIL 1 — Immediate confirmation ─────────────────────────────────────────
e1_body = f"""
              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                We got your request. Someone from our team will follow up within one business day.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                In the meantime, here is what SIGNiX's eNotary platform gives you:
              </p>

              <!-- Skim panel -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
                     style="background-color:{CANVAS};border:1px solid {RULE};border-left:4px solid {GREEN};border-radius:6px;margin-bottom:20px;">
                <tr>
                  <td style="padding:16px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <p style="margin:0 0 10px;font-size:13px;font-weight:700;color:{INK};letter-spacing:0.05em;text-transform:uppercase;">
                      What you get
                    </p>
                    <p style="margin:0 0 8px;font-size:14px;line-height:1.6;color:{BODY};">
                      <strong style="color:{INK};">A PKI-based digital signature</strong> on every notarized document. It holds up in court without calling us.
                    </p>
                    <p style="margin:0 0 8px;font-size:14px;line-height:1.6;color:{BODY};">
                      <strong style="color:{INK};">Built-in identity verification.</strong> ID Verify, KBA, and SMS OTP are standard. You control which steps apply.
                    </p>
                    <p style="margin:0 0 8px;font-size:14px;line-height:1.6;color:{BODY};">
                      <strong style="color:{INK};">A tamper-evident audit trail.</strong> Every session is logged. Every signature is cryptographically sealed.
                    </p>
                    <p style="margin:0;font-size:14px;line-height:1.6;color:{BODY};">
                      <strong style="color:{INK};">We do not hold your documents.</strong> You own the data. It never lives on our servers after the session ends.
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                If you want to move faster, book time directly below. I can show you the platform in 20 minutes and answer any questions you have.
              </p>
"""

shell(
    tag_label="eNotary &amp; Remote Online Notarization",
    subject_a="We got your request. Here is what to expect.",
    subject_b="Your SIGNiX eNotary inquiry.",
    preview="Someone will follow up within one business day. Here is what SIGNiX gives you in the meantime.",
    body_html=e1_body,
    cta_label="Schedule 20 minutes",
    footer_note=(
        "You received this because you submitted an inquiry about SIGNiX's eNotary platform. "
        "If you have questions before we connect, reply to this email."
    ),
    filename="eNotary-Email-1-Confirmation.html",
)


# ── EMAIL 2 — What makes SIGNiX different (Day 3) ────────────────────────────
e2_body = f"""
              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                Most e-signature and eNotary tools capture a click. That click is easy to dispute.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                SIGNiX works differently. We use PKI digital signatures. That means the signer's identity is embedded directly in the document. Not stored in our cloud. Not dependent on our servers. Inside the file, permanently.
              </p>

              <!-- Comparison panel -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
                     style="border:1px solid {RULE};border-radius:6px;margin-bottom:20px;overflow:hidden;">
                <tr style="background-color:{INK};">
                  <td width="50%" style="padding:10px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <p style="margin:0;font-size:12px;font-weight:700;color:{WHITE};letter-spacing:0.08em;text-transform:uppercase;">
                      Standard click-to-sign
                    </p>
                  </td>
                  <td width="50%" style="padding:10px 16px;background-color:{GREEN};">
                    <p style="margin:0;font-size:12px;font-weight:700;color:{WHITE};letter-spacing:0.08em;text-transform:uppercase;">
                      SIGNiX PKI signature
                    </p>
                  </td>
                </tr>
                <tr style="border-bottom:1px solid {RULE};">
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{BODY};">
                    Identity record lives in vendor's cloud
                  </td>
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{INK};font-weight:600;">
                    Identity embedded in the document
                  </td>
                </tr>
                <tr style="border-bottom:1px solid {RULE};background-color:{CANVAS};">
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{BODY};">
                    Tamper proof relies on vendor records
                  </td>
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{INK};font-weight:600;">
                    Cryptographically sealed in the PDF
                  </td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{BODY};">
                    Dispute requires vendor to produce records
                  </td>
                  <td style="padding:12px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:{INK};font-weight:600;">
                    Document proves itself in court
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                For a notarized document, that difference matters. A disputed signature is a legal and operational problem. Yours should hold up on its own, without a phone call to us.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                I can walk you through it in 20 minutes. Book a time below.
              </p>
"""

shell(
    tag_label="eNotary &amp; Remote Online Notarization",
    subject_a="The difference between a click and a proof.",
    subject_b="Why PKI matters for notarized documents.",
    preview="Standard e-signature tools capture a click. A click is easy to dispute. Here is what SIGNiX does instead.",
    body_html=e2_body,
    cta_label="Book 20 minutes with me",
    footer_note=(
        "You received this because you submitted an inquiry about SIGNiX's eNotary platform. "
        "Reply any time if you have questions."
    ),
    filename="eNotary-Email-2-PKI-Difference.html",
)


# ── EMAIL 3 — Social proof (Day 7) ───────────────────────────────────────────
e3_body = f"""
              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                When people ask whether SIGNiX is worth switching to, I usually point them to someone in the same situation.
              </p>

              <!-- Quote card -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
                     style="background-color:{CANVAS};border:1px solid {RULE};border-left:4px solid {GREEN};border-radius:6px;margin-bottom:20px;">
                <tr>
                  <td style="padding:20px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <p style="margin:0 0 12px;font-size:16px;line-height:1.65;color:{INK};font-style:italic;">
                      "There are so many credit unions asking my opinion about SIGNiX, not just because we're using them, but because so many others in the industry have chosen SIGNiX. When asked, I assure them that if they want better security at a fraction of the price, SIGNiX is the right choice."
                    </p>
                    <p style="margin:0;font-size:13px;font-weight:600;color:{MUTED};">
                      Margaret Glover, Business Lending Manager, Atlanta Postal Credit Union
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:{INK};letter-spacing:0.05em;text-transform:uppercase;">
                Why I share this
              </p>
              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                Margaret gets asked about SIGNiX regularly because Atlanta Postal Credit Union uses it and other institutions notice the difference. The security argument lands on its own. The pricing seals it.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                If you have a specific use case in mind, I want to hear it. The 20 minutes goes faster when we start from what you actually need.
              </p>
"""

shell(
    tag_label="eNotary &amp; Remote Online Notarization",
    subject_a="What a credit union like yours told us.",
    subject_b="The question I get asked most.",
    preview="When people ask whether SIGNiX is worth switching to, I usually point them to someone in the same situation.",
    body_html=e3_body,
    cta_label="Talk through your use case",
    footer_note=(
        "You received this because you submitted an inquiry about SIGNiX's eNotary platform. "
        "The quote from Margaret Glover is sourced from the SIGNiX website. "
        "Reply any time to update your preferences."
    ),
    filename="eNotary-Email-3-Social-Proof.html",
)


# ── EMAIL 4 — Direct ask (Day 14) ────────────────────────────────────────────
e4_body = f"""
              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                I want to keep this short.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                You reached out about SIGNiX's eNotary platform. I have sent a few notes. I do not want to keep filling your inbox if the timing is off.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                If you are still interested, book 20 minutes below. I will show you the platform, answer your questions, and we can decide together if it is a fit.
              </p>

              <p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{BODY};">
                If the timing is not right, reply and let me know. I will check back in when it makes more sense.
              </p>

              <!-- Final proof strip -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
                     style="background-color:{INK};border-radius:6px;margin-bottom:24px;">
                <tr>
                  <td style="padding:16px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
                    <p style="margin:0 0 10px;font-size:12px;font-weight:700;color:{GREEN};letter-spacing:0.1em;text-transform:uppercase;">
                      Quick recap
                    </p>
                    <p style="margin:0 0 6px;font-size:14px;line-height:1.6;color:{WHITE};">
                      PKI digital signatures. Identity embedded in the document, not stored in the cloud.
                    </p>
                    <p style="margin:0 0 6px;font-size:14px;line-height:1.6;color:{WHITE};">
                      ID Verify, KBA, and SMS OTP built in. You control the workflow.
                    </p>
                    <p style="margin:0 0 6px;font-size:14px;line-height:1.6;color:{WHITE};">
                      Tamper-evident audit trail on every session.
                    </p>
                    <p style="margin:0;font-size:14px;line-height:1.6;color:{WHITE};">
                      We do not hold your documents. You own the data.
                    </p>
                  </td>
                </tr>
              </table>
"""

shell(
    tag_label="eNotary &amp; Remote Online Notarization",
    subject_a="Still want to see it?",
    subject_b="Last note from me on this.",
    preview="I do not want to fill your inbox if the timing is off. Here is a simple way to move forward or press pause.",
    body_html=e4_body,
    cta_label="Book 20 minutes",
    footer_note=(
        "You received this because you submitted an inquiry about SIGNiX's eNotary platform. "
        "This is the last email in this sequence. Reply any time and I will pick things back up."
    ),
    filename="eNotary-Email-4-Final-Ask.html",
)

print(f"\nAll 4 eNotary emails written to {OUTPUT_DIR}")
