# SIGNiX Design Guidelines

Design tokens and typographic conventions derived from production SIGNiX collateral (Mike fraud insights email, March 2026). Use these standards for every document, email, HTML output, or visual artifact produced in this workspace.

**Last updated:** 2026-04-02

---

## Color palette

| Token | Hex | Usage |
|---|---|---|
| Brand green | `#6da34a` | CTAs, links, key highlights, eyebrow labels, accent rules |
| Ink / headline | `#2e3440` | Headlines, strong copy, bold emphasis |
| Body text | `#545454` | Paragraph text, general copy |
| Muted / footnote | `#6b7280` | "Mike's use" callouts, footnotes, secondary annotations |
| Dividers | `#d8dee9` | Horizontal rules, card borders, section separators |
| Panel / card background | `#eceff4` | Callout boxes, info panels, card backgrounds |
| Page / email canvas | `#f8fafb` | Outermost background for emails and documents |

---

## Typography

### Font stack

```
-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif
```

No external web font dependency. Renders as:
- **San Francisco** on macOS / iOS
- **Segoe UI** on Windows
- **Roboto** on Android / Chrome OS

This is deliberate — inbox-safe, no render delay, no external request.

---

### Type scale

| Role | Size | Weight | Color | Notes |
|---|---|---|---|---|
| Eyebrow / section label | `11px` | `600` | `#6da34a` | `letter-spacing: 0.14em`, uppercase |
| Body / intro copy | `16px` | normal | `#545454` | `line-height: 1.55` |
| Article headline / link | `15px` | normal | `#2e3440` | `line-height: 1.5` |
| Article body | `14px` | normal | `#545454` | `line-height: 1.5` |
| Callout / annotation | `13px` | normal | `#6b7280` | `line-height: 1.45` |
| Small caps label (IT / compliance) | `13px` | `700` | `#6da34a` | `letter-spacing: 0.06em`, uppercase |
| Footer / legal disclaimer | `11px` | normal | `#6b7280` | `line-height: 1.45` |
| Links | contextual | `600` | `#6da34a` | `text-decoration: none` |
| Strong / bold emphasis | contextual | `700` | `#2e3440` | — |

---

## Spacing and layout conventions

| Element | Value |
|---|---|
| Section padding (email cell) | `24px 28px` (top/bottom, left/right) |
| Paragraph margin (standard) | `0 0 14px` |
| Paragraph margin (loose body) | `0 0 16–20px` |
| Divider padding above footer | `padding-top: 16px` |
| Card / panel border | `1px solid #d8dee9` |

---

## Logo

- **Format:** PNG (hosted via HubSpot CDN from signix.com)
- **Usage:** Top of emails and documents, left-aligned or centered depending on layout
- Two variants: full logo and icon-only — confirm which applies per deliverable

---

## Design principles

1. **System fonts only** — never introduce an external font dependency unless explicitly required.
2. **Green for action and accent** — `#6da34a` is reserved for CTAs, links, and eyebrow labels. Don't use it for body text.
3. **Ink for authority** — `#2e3440` signals importance; use for headlines and bolded key terms.
4. **Hierarchy through size and weight** — avoid decorative elements; let scale and weight do the work.
5. **Whitespace is intentional** — generous padding inside sections; tight margins between related elements.
6. **Partner-first tone** — visual design should feel professional and trustworthy, not salesy. Clean over clever.

---

## Typography principles (Butterick's Practical Typography)

Rules sourced from [practicaltypography.com](https://practicaltypography.com) — the definitive reference for document and web typography. Applied here to SIGNiX deliverables.

### Body text: the four foundations

These four choices determine how readable every document feels. Get these right before anything else.

| Property | Rule | SIGNiX application |
|---|---|---|
| **Font size** | 15–25px on the web; 10–12pt in print | Use `15–16px` for body; `14px` for compact sections |
| **Line spacing** | 120–145% of font size | Our `line-height: 1.55` (155%) is slightly generous — fine for email; tighten to `1.45` for dense document sections |
| **Line length** | 45–90 characters per line | Constrain content columns to ~600px max; avoid full-bleed text blocks |
| **Font choice** | Use a professional or well-chosen system font; never Times New Roman or Arial | Our system stack (`-apple-system, Segoe UI, Roboto`) is correct — clean, inbox-safe, no external dependency |

---

### Emphasis: bold and italic

- **Bold and italic are mutually exclusive** — never combine them.
- **Use both as little as possible.** If everything is emphasized, nothing is.
- **SIGNiX uses a sans-serif stack** — per Butterick, skip italic for sans-serif and use **bold only** for emphasis. Italic on sans-serif produces only a gentle slant that doesn't register clearly.
- Bold is for terms, phrases, or short strings — not whole sentences or paragraphs.
- Never underline, except for hyperlinks.

---

### Headings

- **Limit to two or three levels maximum.** More than three levels confuses readers. Two is preferred.
- Headings are signposts for the argument, not every topic and subtopic.
- **Use space above and below** as the primary means of emphasis — it is subtle and effective.
- **Use bold, not italic** for headings (reinforces the sans-serif rule above).
- Size increases should be small increments — just enough to signal hierarchy, not dramatic jumps.
- Never underline headings. Never center headings except for cover pages or titles.
- Never use all-caps for full headings (fine for short eyebrow labels — which we already do at `11px` with `letter-spacing: 0.14em`).

---

### All caps and letterspacing

- All caps are acceptable for **less than one line** of text (our eyebrow labels qualify).
- Always add **5–12% extra letterspacing** when using all caps — matches our `letter-spacing: 0.14em` (14%) convention, which is at the generous end and works well at small sizes.

---

### Paragraph spacing

- Choose **either** first-line indents **or** space between paragraphs — never both.
- For emails and web documents: use `margin-bottom` (space between paragraphs). Our `0 0 14–20px` paragraph margins are correct.

---

### Punctuation discipline

- One space between sentences (never two).
- Use curly/smart quotes, not straight quotes.
- Use proper em dashes (—), not double hyphens (--).
- One exclamation point per document is plenty in formal business writing.

---

### Alignment

- **Left-align body text** as the default. Centered text is for short display copy only.
- Avoid justified text in web contexts unless hyphenation is also enabled.

---

## Source

**SIGNiX brand tokens** confirmed from `06-DOCS/mike-fraud-insights-email-MARCH-2026/mike-march-2026-fraud-insights-email-BLEND.html` — the recommended production variant of SIGNiX's March 2026 partner email. Color palette also cross-referenced with `06-DOCS/PROJECT-MIKE-MARKET-INSIGHTS-EMAIL.md` (line 25).

**Typography principles** sourced from [Butterick's Practical Typography](https://practicaltypography.com) — *Typography in Ten Minutes* and *Summary of Key Rules* chapters, plus *Bold or Italic* and *Headings* chapters. Retrieved 2026-04-02.
