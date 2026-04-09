# Google Ads Campaign Setup and Management Guide
## SIGNiX — Search Campaigns

**Last updated:** April 9, 2026
**Author:** Chris Teague, Head of Growth and Marketing
**Applies to:** All new SIGNiX Search campaigns

---

## Before you open Google Ads

Do these four things first. If any are missing, stop and fix them before building.

| Checklist | Status |
|---|---|
| Ad copy written (15 headlines, 4 descriptions per campaign) | Must have |
| Keywords selected and formatted with quote marks for phrase match | Must have |
| Landing page URL confirmed (signix.com/demo) | Must have |
| Conversion tracking confirmed with Jake (demo form fires Google Ads event) | Must have before switching to Smart Bidding |

---

## Part 1 — Building a new campaign

### Step 1 — Start a new campaign

1. Go to **google.com/ads** and sign in
2. Click **Campaigns** in the left nav
3. Click the blue **+ New campaign** button

### Step 2 — Choose objective and type

- **Objective:** Leads
- **Campaign type:** Search
- **Goal:** Submit lead forms *(not "Contacts," not "Qualified leads" — those require additional HubSpot setup)*

> **Do not select Google's native lead form.** Always use your own website form. Google's lead form sends data to Google, not HubSpot. You lose response time tracking, rep routing, and closed-loop reporting.

### Step 3 — Enter your website URL

```
https://www.signix.com/demo
```

Use the specific demo page, not the homepage. The homepage forces visitors to hunt for the form. The demo page puts them one click from converting.

### Step 4 — Bidding

**Always choose "Clicks" (Maximize clicks) for new campaigns.**

- Check the box: **"Set a maximum CPC bid limit"**
- Enter: **$5.00**

> **Why not Maximize Conversions or Target CPA?** Google needs 30–50 conversions in 30 days before Smart Bidding works. A brand new campaign has zero. Without data, Google will either underspend or burn budget chasing conversions it can't find. Start on Manual CPC. Switch to Smart Bidding in month 2 once data exists.

> **Watch out:** Google defaults to Maximize Clicks without a bid cap. Always set the $5.00 cap manually or you have no ceiling on cost-per-click.

### Step 5 — Networks

When you see the Networks section:

- **Keep checked:** Google Search Network, Search partners
- **Uncheck:** Display Network

> **Display Network will waste your budget.** It shows banner ads on third-party websites — wrong audience, wrong format for B2B lead gen. Always uncheck it. Google checks it by default every time.

### Step 6 — Location and language

- Location: United States
- Language: English

### Step 7 — Skip these sections

Google will show you several sections during the builder. Skip all of these:

| Section | What to do | Why |
|---|---|---|
| AI Max | Skip / turn off | Rewrites your headlines and expands keywords without your input |
| AI-generated ad suggestions | Skip | Use your own copy — it's already written |
| Audience segments | Skip for now | Add in observation mode only after 4–6 weeks of data |
| Images | Skip | Search campaigns don't show images |
| Sitelinks | Skip for launch | Add later once campaigns are running |
| "Add more keywords" suggestions | Skip | Google broadens targeting — stick to your list |

### Step 8 — Keywords and ads

**Entering keywords:**

Type each keyword with quote marks to set phrase match:

```
"are electronic signatures legally binding"
"digital signatures pki"
```

- **Phrase match** (`"keyword"`) — shows ads when the search contains your keyword
- **Broad match** (`keyword`) — shows ads for loosely related searches, burns budget fast
- **Exact match** (`[keyword]`) — shows ads only for that exact search, too restrictive to start

> **Always use phrase match for new campaigns.** Move to exact match on specific keywords only after 30+ conversions prove intent.

**Entering ad copy:**

Google will pre-fill headline fields with content pulled from your website. **Delete all of it.** Use only the copy from `PROJECT-DOCS/SIGNiX_GoogleAds_4.9.26.docx`.

- Enter 15 headlines, one per field (30 characters max each)
- Enter 4 descriptions (90 characters max each)
- **Pin headline 1** to position 1 (fear hook or primary benefit)
- **Pin the CTA headline** to position 3 ("Request a Demo Today")
- Leave all other headlines unpinned — Google optimizes the rest

> **The ad strength meter will show "Poor" or "Average."** Ignore it. It rewards keyword stuffing and variety of character lengths, not conversion quality. Our copy is intentionally clean. A "Poor" ad strength score with strong copy will outperform a "Good" score with weak copy every time.

**Display path:**

The two path fields customize how your URL appears in the ad. They don't change where the click goes.

```
Campaign: Compliance / Legal → legal / signatures
Campaign: RON Institutional  → ron / notary
Campaign: Healthcare/Consent → hipaa / consent
Campaign: Wealth Management  → wealth / advisors
Campaign: Auth / PKI         → auth / identity
```

### Step 9 — Ad rotation (advanced settings)

If Google shows an ad rotation option, select:

**Optimize: Prefer best performing ads**

This lets Google show the headline/description combinations that get the most clicks. Do not select "Do not optimize" unless you are running a controlled A/B test.

### Step 10 — Budget

Enter the daily budget from the campaign plan. Do not accept Google's suggested budget — it will always be higher than yours.

| Campaign | Daily Budget |
|---|---|
| Compliance / Legal | $17/day |
| RON Institutional | $10/day |
| Healthcare / Consent | $15/day |
| Wealth Management | $10/day |
| Auth / PKI | $10/day |

> **Total account budget cap: $100/day = $3,000/month.** Before adding any new campaign budget, confirm the total stays at or under $100/day. If adding Phase 2 campaigns, reduce an existing campaign first or get approval to increase the monthly budget.

### Step 11 — Publish

Click **Publish campaign**. Google may ask you to verify your identity — confirm. The campaign will go live immediately with status "Eligible (Learning)."

---

## Part 2 — Settings to fix after publishing

The campaign builder does not expose all settings. Fix these immediately after every new campaign publishes.

### How to get to Campaign Settings

> **Navigation tip:** This is the hardest part to find. The Settings tab is in gray font and easy to miss.

1. Click **Campaigns** in the left nav
2. You will see tabs at the top of the page: **Campaigns | Drafts | Settings** — the Settings tab is gray, not blue
3. Click **Settings**

Alternatively:
1. Click the blue campaign name link in the campaigns list
2. Once inside the campaign, look for a Settings option in the left nav or at the top

### Fix 1 — Bidding (if it defaulted to Maximize Clicks without a cap)

1. In Campaign Settings, find the **Bidding** section
2. Click to edit
3. Change to **Manual CPC**
4. Check **"Set a maximum CPC bid limit"**
5. Enter **$5.00**
6. Save

### Fix 2 — Networks (if Display Network is still checked)

1. In Campaign Settings, find the **Networks** section
2. Click to edit
3. Uncheck **Display Network**
4. Keep Google Search Network and Search partners checked
5. Save

### Fix 3 — Ad schedule

1. In Campaign Settings, scroll to **Ad schedule** (also accessible from the left nav)
2. Click to edit
3. Set: **Monday through Friday, 9:00 AM – 5:00 PM, Eastern Time**
4. Save

> **Why M–F 9–5 only?** SIGNiX sells to business buyers. Nobody submits a B2B demo request at 2 AM on Saturday. Before this restriction was added, 31% of spend ran outside business hours with zero conversions. That's over $1,500/month wasted.

---

## Part 3 — What to do when Google asks you things

Google presents recommendations and prompts constantly. Here is how to handle the common ones:

| Google prompt | What to do |
|---|---|
| "Improve your ad strength" | Ignore. Our copy is intentional. |
| "Add more keywords (+X%)" | Skip. Google broadens targeting. |
| "Enable AI Max" | Turn off. It overwrites your copy and expands your URLs. |
| "Add sitelinks" | Skip at launch. Add after 4 weeks once campaigns are running. |
| "Switch to Maximize Conversions" | Ignore until you have 30+ conversions in 30 days. |
| "Add images to your campaign" | Skip for Search campaigns. Images are for Display/Performance Max. |
| "Include popular keywords" | Skip. Stick to the validated keyword list. |
| Ads Advisor panel (right side) | Close it. It's Google's AI assistant and will suggest changes that conflict with your strategy. |

---

## Part 4 — Ongoing management checklist

### Weekly (every Monday)

- [ ] Check spend vs. budget — confirm no campaign is overspending
- [ ] Review search terms report — add any irrelevant terms to the negative keyword list
- [ ] Note any new "Eligible (Limited)" flags and investigate cause

### Monthly (first Monday of each month)

- [ ] Pull fresh Google Ads CSV exports and re-run the dashboard script
- [ ] Review keyword performance — pause any keyword with >$50 spend and zero conversions
- [ ] Check conversion count — if any campaign has 30+ conversions, evaluate switching to Maximize Conversions
- [ ] Review click-through rate by campaign — CTR below 2% on a keyword needs new ad copy or removal

### At 4–6 weeks (Phase 2 decision point — May 7, 2026)

- [ ] Review Phase 1 performance: cost per click, impressions, clicks, conversions
- [ ] Confirm Jake has verified conversion tracking is firing
- [ ] Decide whether to launch Phase 2 campaigns (Healthcare/Consent, Wealth Mgmt, Auth/PKI)
- [ ] If launching Phase 2, confirm budget reallocation stays at $100/day total

---

## Part 5 — Decision rules

Use these to make keyword and budget decisions without second-guessing.

**Pause a keyword if:**
- Spent more than $50 AND zero conversions AND running more than 2 weeks

**Keep a keyword if:**
- Spent less than $20 (not enough data yet)
- It is a branded term
- It is a core RON term with proven volume

**Switch to Maximize Conversions if:**
- Campaign has 30+ conversions in the last 30 days
- Conversion tracking is confirmed firing
- Campaign has been running at least 6 weeks

**Reduce a campaign budget if:**
- Cost per conversion exceeds $200 for 3 consecutive weeks
- Click-through rate drops below 1% and copy refresh hasn't helped

**Pause a campaign if:**
- Zero impressions after 2 weeks (keyword volume issue — run Keyword Planner)
- Status shows "Limited" with no improvement after fixing bidding and targeting

---

## Part 6 — Current campaign inventory (as of April 9, 2026)

| Campaign | Phase | Budget | Rep | Keywords | Status |
|---|---|---|---|---|---|
| (Arcb) Branded - V1.1 | Existing | $33/day | — | Brand terms | Eligible |
| (Arcb) RON - V1.1 | Existing | $40/day | Sam | RON terms | Eligible (Limited) |
| Compliance / Legal | Phase 1 | $17/day | Aspen | 5 keywords | Eligible (Learning) |
| RON Institutional | Phase 1 | $10/day | Sam | 2 keywords | Eligible (Learning) |
| Healthcare / Consent | Phase 2 | $15/day | Aspen + Chris | 3 keywords | Not yet built |
| Wealth Management | Phase 2 | $10/day | Aspen | 1 keyword | Not yet built |
| Auth / PKI | Phase 2 | $10/day | Aspen | 1 keyword | Not yet built |

**Total at Phase 1:** $100/day = $3,000/month
**Total at Phase 2 (requires budget decision):** $135/day — requires either increasing budget or reducing existing campaigns

---

## Quick reference — Key account settings

| Setting | Value |
|---|---|
| Account | signixmarketing@gmail.com |
| Monthly budget cap | $3,000 ($100/day) |
| Landing page | https://www.signix.com/demo |
| Conversion goal | Submit lead forms |
| Ad schedule | Monday–Friday, 9 AM–5 PM EST |
| Bidding strategy (new campaigns) | Manual CPC, $5.00 max |
| Match type (new keywords) | Phrase match |
| Networks | Search + Search partners only (no Display) |
| Conversion tracking contact | Jake (confirm demo form fires GA4/Google Ads event) |

---

*Source of truth: `PROJECT-DOCS/GOOGLE-ADS-SETUP-GUIDE.md`*
*Ad copy source: `PROJECT-DOCS/SIGNiX_GoogleAds_4.9.26.docx`*
*Keyword source: `PROJECT-DOCS/SIGNiX_Keyword_Master_4.6.26.xlsx`*
