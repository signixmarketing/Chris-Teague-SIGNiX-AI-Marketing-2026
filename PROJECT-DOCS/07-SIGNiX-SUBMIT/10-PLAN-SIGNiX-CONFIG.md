# Plan: SIGNiX Configuration (Plan 1)

This document outlines how to add **SignixConfig** (SIGNiX credentials and submitter information) and the **SIGNiX Configuration** administrative page. There is a single configuration record (singleton); the page allows staff to create or edit it. This plan does not implement the submit flow—only the model and UI so that configuration exists for the transaction packager (later plans).

**Design reference:** [DESIGN-SIGNiX-SUBMIT.md](DESIGN-SIGNiX-SUBMIT.md) — Section 4.4 (SIGNiX configuration), Section 6.2 (Configuration), Section 7.6 (Administrative — SIGNiX configuration). [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) — Flex API credentials and endpoints.

**Prerequisites:** [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) plans 1–4 and PHASE-PLANS-DOCS plans 1–4 are implemented. The app has Deals, Document Sets, and the Send for Signature stub.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines batches and verification.

---

## 1. Goals and Scope

- **Model:** A `SignixConfig` model storing a single record: Flex API credentials (sponsor, client, user_id, password, workgroup), demo_only, delete_documents_after_days, default_email_content, and submitter fields (first_name, middle_name, last_name, email, phone). Used by the transaction packager when building SubmitDocument.
- **Singleton:** Only one row is used. The UI always loads or creates that one record (e.g. by fixed primary key or get_or_create with defaults).
- **UI:** One page — **SIGNiX Configuration** — with a form to view/edit the single config. No list view. Access restricted to staff (or a dedicated permission).
- **Out of scope this plan:** Calling the Flex API, Send for Signature behavior, or any use of the config beyond saving/loading.

---

## 2. Model: SignixConfig

- **App:** `apps.deals` (same app as the transaction packager and SignatureTransaction per design).
- **Persistence:** SQLite (existing database). One table; one row.

**Fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `sponsor` | CharField(max_length=255, blank=True) | Flex API Sponsor (CustInfo). Required in form for save. |
| `client` | CharField(max_length=255, blank=True) | Flex API Client (CustInfo). Required in form for save. |
| `user_id` | CharField(max_length=255, blank=True) | Flex API User id (CustInfo). Required in form for save. |
| `password` | CharField(max_length=255, blank=True) | Flex API Password (CustInfo). Store with appropriate protection per security policy; use password input in forms. Required in form for initial save; on edit, blank means “keep existing”. |
| `workgroup` | CharField(max_length=255, blank=True) | Flex API Workgroup (CustInfo). **Must match the exact value** assigned by SIGNiX for your client (case-sensitive; a typo such as SSD instead of SDD causes "workgroup does not exist"). Required in form for save. |
| `demo_only` | BooleanField(default=True) | When True, use Webtest endpoint; when False, use Production. |
| `delete_documents_after_days` | PositiveIntegerField(default=60) | Maps to Flex DelDocsAfter (retention). |
| `default_email_content` | TextField(default=… see below) | Used for EmailContent in SubmitDocument. Default: `"Your documents for the Sample Application are available online for viewing and signing."` |
| `submitter_first_name` | CharField(max_length=150, blank=True) | Submitter first name (Data block). |
| `submitter_middle_name` | CharField(max_length=150, blank=True) | Submitter middle name. |
| `submitter_last_name` | CharField(max_length=150, blank=True) | Submitter last name. |
| `submitter_email` | EmailField(max_length=254, blank=True) | Submitter email (required for submit; validated in submit flow or in form clean). |
| `submitter_phone` | CharField(max_length=30, blank=True) | Submitter phone; default `"800-555-1234"` used by packager when blank and Flex requires it. |

**Conventions:**

- `__str__`: e.g. `"SIGNiX Configuration"` or `"SIGNiX Config (Webtest)"` / `"SIGNiX Config (Production)"` based on `demo_only`.
- `Meta`: `verbose_name = "SIGNiX configuration"`, `verbose_name_plural = "SIGNiX configurations"`.
- **Singleton:** Use a fixed primary key (e.g. `pk=1`) or a helper that does `get_or_create` with defaults so only one row exists. Credentials and submitter fields are allowed blank on the model so the single row can be created with defaults (demo_only=True, delete_documents_after_days=60, default_email_content=…); the form requires credentials and submitter_email when saving so that once saved, the config is valid for submit.

**Password storage:** Store the password in the database; use a password input widget in forms so it is not visible in the browser. See Section 8 for the note on addressing password storage before Production deployment.

---

## 3. Helper: get_signix_config()

- **Location:** e.g. `apps.deals.signix` module (create `apps/deals/signix.py`) or in `apps.deals/models.py` as a function. Design references `get_signix_config()` as the way the packager loads config.
- **Behavior:** Return the single `SignixConfig` instance. If no row exists, create one with default values (demo_only=True, delete_documents_after_days=60, default_email_content=…, other fields blank or default) and return it. This allows the submit flow to call `get_signix_config()` and get a record; validation will then require credentials and submitter_email to be set before allowing submit.
- **Signature:** `get_signix_config() -> SignixConfig`

---

## 4. SIGNiX Configuration Page

### 4.1 URL and access

- **URL:** `/signix/config/` (name `signix_config`).
- **Access:** Restrict to staff users (e.g. `@user_passes_test(lambda u: u.is_staff)` or `UserPassesTestMixin` with `is_staff`). Design allows “staff/superuser or a dedicated configurator permission”; implement staff-only for this plan.
- **Method:** GET shows the form (create or edit the single config); POST saves and redirects back with a success message.

### 4.2 Form

- **Form:** ModelForm for `SignixConfig` with all fields. Group fields in the template:
  1. **Credentials:** sponsor, client, user_id, password, workgroup. All five are **required in the form** when saving (so that once saved, the config is valid for submit).
  2. **Submitter:** submitter_first_name, submitter_middle_name, submitter_last_name, submitter_email, submitter_phone. Require **submitter_email** in form validation. Other submitter fields optional.
  3. **Settings:** demo_only (checkbox), delete_documents_after_days (number), default_email_content (textarea).
- **Password:** Use `forms.PasswordInput` (or `widget=forms.PasswordInput(render_value=True)` on edit so the field can show “••••••” or leave blank to keep existing). Optional: `attrs={"autocomplete": "new-password"}` to reduce browser prompts. **Validation:** Require the password field when the instance has no password set (e.g. `not instance.password`). When the instance already has a password, a blank password field means “keep existing”—do not update `instance.password` in `save()` (implement in view or form `save(commit=False)` + set password only when the form’s password value is non-empty).
- **Defaults:** Pre-fill default_email_content and delete_documents_after_days when creating the singleton.

### 4.3 Template

- **Template:** `templates/deals/signix_config_form.html`. Extend `base.html`. Card/section layout: Credentials, Submitter, Settings. Submit button: “Save configuration”. Success message after POST.
- **Navigation:** Add a **SIGNiX Configuration** link in the sidebar (or under a Settings/Admin group) visible to staff, pointing to `{% url 'signix_config' %}` or the named URL used. Design: “main menu or sidebar item (e.g. SIGNiX Configuration or under Settings/Admin area)”. Use sidebar for consistency with the rest of the app.

### 4.4 View

- **View:** Function-based or class-based. On GET: get or create the singleton (e.g. `get_signix_config()`), pass to form as instance. On POST: bind form, validate, save. Redirect to same page (or a “view” page) with success message. Handle password: if password field is blank on edit, **either** remove it from `cleaned_data` and do not update the password field on the model, **or** (simpler) after `form.save(commit=False)` set `instance.password = SignixConfig.objects.get(pk=instance.pk).password` when the form’s password value is empty, then call `instance.save()` so the existing password is preserved.

---

## 5. URLs and Navigation

- **Config URL:** In `config/urls.py`, add `path("signix/config/", view, name="signix_config")` and import the view from `apps.deals.views` (e.g. `from apps.deals.views import signix_config_edit`). Use this single path (no separate signix_urls include) for simplicity.
- **Sidebar:** In `templates/base.html`, add a link “SIGNiX Configuration” → `{% url 'signix_config' %}`. Show only to staff: `{% if user.is_staff %} ... {% endif %}`.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Model and helper (steps 1–4)

1. **SignixConfig model**
   - In `apps/deals/models.py`, add `SignixConfig` with all fields from Section 2. Use `default` for `default_email_content` (the long string), `delete_documents_after_days=60`, `demo_only=True`. Add `__str__` and `Meta`.
   - Run `python manage.py makemigrations deals` and `python manage.py migrate`.

2. **Singleton behavior**
   - Use **`SignixConfig.objects.get_or_create(pk=1, defaults={...})`** in `get_signix_config()`: first call creates the row with id=1 and default values; subsequent calls return that row. Do not create an initial row in migrations. The defaults dict must include all fields that have non-blank defaults (demo_only=True, delete_documents_after_days=60, default_email_content=…).

3. **get_signix_config()**
   - Create `apps/deals/signix.py`. Implement `get_signix_config()` that returns the single record: `SignixConfig.objects.get_or_create(pk=1, defaults={...})`. Defaults: demo_only=True, delete_documents_after_days=60, default_email_content per design (the full string), other fields blank or model default.

4. **Verification (Batch 1)**
   - Django check passes. Migrate. In shell: `from apps.deals.signix import get_signix_config; c = get_signix_config(); assert c.demo_only is True; assert c.delete_documents_after_days == 60`. Create a second record manually (if no unique constraint) and document that the UI always edits the first or a fixed pk—or add a unique constraint so only one row can exist (e.g. a constant “slug” or use id=1 only).

### Batch 2 — Form, view, URL, template (steps 5–10)

5. **Form**
   - In `apps/deals/forms.py`, add `SignixConfigForm` ModelForm with all fields. Require all five credentials and submitter_email when saving (see Section 4.2). Password widget: `PasswordInput(render_value=True)`. Require password in form validation only when the instance has no password set; when instance has a password, blank field means keep existing—in `save()` (or in the view), set `instance.password` only when the form’s password value is non-empty.

6. **View**
   - Add `signix_config_edit` (or `signix_config`) view in `apps/deals/views.py`. Decorate with `@login_required` and `@user_passes_test(lambda u: u.is_staff)`. GET: get_signix_config(), pass to form as instance. POST: bind form, if valid save (with password handling), redirect to same URL with success message. Use `redirect('signix_config')` or the named URL.

7. **URL**
   - In `config/urls.py`, add `path("signix/config/", signix_config_edit, name="signix_config")` and import: `from apps.deals.views import signix_config_edit` (or add to existing deals view imports).

8. **Template**
   - Create `templates/deals/signix_config_form.html`. Extend base. Form with csrf_token, form.as_p or form fields grouped (Credentials, Submitter, Settings). Submit button. Display non-field errors. Use Bootstrap/card layout consistent with the app. If using Bootstrap, apply `form-control` to inputs in the form’s `__init__`; use `form-check-input` for the `demo_only` checkbox (not `form-control`).

9. **Sidebar**
   - In `templates/base.html`, add “SIGNiX Configuration” link for staff users (`{% if user.is_staff %}`), linking to `{% url 'signix_config' %}`. Place after other main nav items (e.g. after Document Set Templates or in an Admin/Settings group if one exists).

10. **Verification (Batch 2)**
    - Log in as staff. Open SIGNiX Configuration. Form loads (singleton created if first time). Save with all fields filled; reload and confirm values persist. Edit and leave password blank; save; confirm password unchanged. Log in as non-staff; confirm SIGNiX Configuration link is not visible (or URL returns 403). Run `get_signix_config()` in shell and confirm it returns the saved instance.

---

## 6a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps below.

### Batch 1 — Model and helper

**Includes:** SignixConfig model in apps.deals, migrations, singleton get_or_create or fixed pk, get_signix_config() in apps.deals.signix (or equivalent).

**How to test after Batch 1:**

1. **Django check:** `python manage.py check` — no issues.
2. **Migrate:** `python manage.py migrate` — deals migration applied.
3. **get_signix_config():** In shell, `from apps.deals.signix import get_signix_config; c = get_signix_config()`. Assert `c.pk` is set, `c.demo_only is True`, `c.delete_documents_after_days == 60`, `c.default_email_content` matches design default. Call again; same record returned (no duplicate).
4. **Optional:** Add a unique constraint or document that only one row is used (e.g. always pk=1). If using get_or_create(pk=1, defaults={...}), first call creates the row; second call gets it.

Batch 1 is complete when the above pass.

### Batch 2 — Form, view, URL, template, sidebar

**Includes:** SignixConfigForm (with password handling), signix_config_edit view (staff-only), URL /signix/config/, template, sidebar link for staff.

**How to test after Batch 2:**

1. **Staff access:** Log in as staff (e.g. karl). Sidebar shows “SIGNiX Configuration”. Open `/signix/config/`; form loads with singleton data (defaults or previously saved).
2. **Save:** Fill credentials, submitter (at least submitter_email), and settings. Submit. Success message; reload shows saved values.
3. **Password:** Change password, save. Reload; change another field but leave password blank; save. Confirm password is still the changed value (not cleared).
4. **Non-staff:** Log out; log in as non-staff user (or create one). SIGNiX Configuration link not visible. Visit `/signix/config/` directly; expect 403 or redirect to login.
5. **get_signix_config():** After saving via UI, in shell run `get_signix_config()` and assert stored values match (e.g. sponsor, submitter_email).

Batch 2 is complete when all of the above pass.

---

## 7. File and URL Summary

| Item | Value |
|------|--------|
| App | `apps.deals` |
| Model | `SignixConfig` (Section 2) |
| Helper | `get_signix_config()` in `apps.deals.signix` |
| URL | `/signix/config/` — name `signix_config` |
| View | `signix_config_edit` (or `signix_config`) — staff only |
| Form | `SignixConfigForm` — all fields, password widget, submitter_email required |
| Template | `templates/deals/signix_config_form.html` |
| Nav | Sidebar: “SIGNiX Configuration” (staff only) → `/signix/config/` |

---

## 8. Open Issues / Notes

- **Password storage:** For this first release, the password may be stored in the database in plain text (with a password input in the UI so it is not visible in the browser). **Before deploying the app to a Production environment (in a later release), the password storage approach must be addressed**—e.g. encryption at rest, a secrets manager, or environment-based secrets—per your security policy.
- **Permission:** Design allows “dedicated configurator permission”; this plan uses `is_staff`. A custom permission can be added later.
- **Workgroup:** Value must match the exact Workgroup string assigned by SIGNiX (case-sensitive); typo causes "workgroup does not exist" on submit.
- **Singleton enforcement:** If you allow multiple rows by mistake, the packager will use `get_signix_config()` which returns one; document that the UI should only ever show/edit that one (e.g. always pk=1 or the first row). A database constraint (e.g. check that id=1 or a single-row table) can be added in a follow-up if desired.

---

## 9. Implementation Notes (from Plan 1 implementation)

- **default_email_content in one place:** Define a constant (e.g. `DEFAULT_SIGNIX_EMAIL_CONTENT`) in `apps/deals/models.py` and use it for both the `SignixConfig.default_email_content` model default and in `get_signix_config()`'s `defaults` dict so the string is not duplicated.
- **Password "keep existing" in the view:** A simple approach: after `form.is_valid()`, do `instance = form.save(commit=False)`. If `instance.pk` and `not form.cleaned_data.get('password')`, set `instance.password = SignixConfig.objects.get(pk=instance.pk).password`. Then `instance.save()`. The view must import `SignixConfig` from `apps.deals.models`.
- **Bootstrap form classes:** In the form's `__init__`, loop over `self.fields` and set `widget.attrs.setdefault('class', 'form-control')` for text/email/number/textarea fields. For the `demo_only` BooleanField use `form-check-input` instead so the checkbox is styled correctly.
- **URL namespace:** The path is registered in `config/urls.py` (project root), so the URL name is `signix_config` with no app prefix. Use `{% url 'signix_config' %}` in templates.

---

*End of plan. Proceed to implementation only after review. Next: [20-PLAN-SIGNiX-SIGNATURE-TRANSACTION.md](20-PLAN-SIGNiX-SIGNATURE-TRANSACTION.md) (Plan 2).*
