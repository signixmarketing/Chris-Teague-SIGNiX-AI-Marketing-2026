# Lease Origination Sample Application — Implementation Plan

This document outlines the plan for building a Django-based **vehicle lease** origination sample application—specifically for **jet pack** leasing—that will later integrate SIGNiX digital signing. The initial phase focuses on authentication, user profiles, and admin—using Django Admin and Jazzmin with SQLite.

**How to use this plan:** Follow **Section 13** (Implementation Order) step by step to build the project from scratch. Use **Section 14** for batching and verification. When implementing UI, auth, or Admin, follow **Section 12.1** to avoid the 500/405 errors and layout issues described there. All setup and run instructions are in Section 14 (no separate README).

**Design:** DESIGN-BASELINE.md. **Knowledge:** KNOWLEDGE-APP-FOUNDATION.md.

---

## 1. Goals and Scope

- **Purpose**: Showcase how to add SIGNiX digital signing to an application; this repo will serve as a reference implementation.
- **Domain**: The application is for **vehicle leasing**, with **jet packs** as the vehicle type (lease origination, documents, and signing will center on jet pack leases).
- **Audience**: Developers integrating SIGNiX; code should be clean, readable, and well-commented.
- **Initial scope**: Lease officer login, user profile (view/edit), and Admin for user management. SIGNiX integration will be added in a later phase.

---

## 2. Technology Stack

| Component   | Choice    | Notes                                                |
|------------|-----------|------------------------------------------------------|
| Framework  | Django    | Current LTS (e.g. 5.x); standard project layout     |
| Admin UI   | Django Admin + Jazzmin | Themed admin; menu and branding          |
| Database   | SQLite    | No external DB; easy to run and demo                 |
| Auth       | Django `django.contrib.auth` | Built-in user model + custom profile |
| Repo       | Git / GitHub | `.gitignore`, structure suitable for GitHub; setup/run in this plan (no separate README) |

---

## 3. Required Modules

The following Python packages will be listed in `requirements.txt` (with version pins for reproducibility):

| Module     | Purpose |
|------------|--------|
| Django     | Web framework; includes auth, admin, ORM, templates. Use current LTS (e.g. 5.x). |
| django-jazzmin | Admin theme and sidebar menu for Django Admin. |

No additional packages are required for the initial version (SQLite and the auth system are part of Django). Optional: pin a minor version for Django (e.g. `Django>=5.0,<6`) and a compatible Jazzmin version.

---

## 4. Project Structure (High Level)

```
django-lease/
├── manage.py
├── requirements.txt
├── PLAN-BASELINE.md
├── .gitignore
├── .vscode/                # Cursor/VS Code Run and Debug
│   ├── launch.json        # Django runserver debug configuration
│   └── settings.json      # (optional) Python interpreter path to project venv
├── config/                 # Project settings package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── users/              # User profile and lease-officer logic
│   │   ├── __init__.py
│   │   ├── models.py       # LeaseOfficerProfile
│   │   ├── admin.py        # (optional; not registered in this plan)
│   │   ├── views.py        # Profile view, profile edit, root_redirect
│   │   ├── urls.py         # app_name='users'; profile, profile/edit
│   │   ├── forms.py        # Profile edit form
│   │   ├── apps.py         # AppConfig name='apps.users'
│   │   ├── migrations/
│   │   └── management/commands/
│   │       └── setup_initial_user.py
│   └── (future: jet pack leases, signing, etc.)
├── templates/
│   ├── base.html           # App pages: sidebar + content (matches Admin look)
│   ├── base_plain.html     # Login / logged_out (no sidebar)
│   ├── admin/
│   │   └── base.html      # Override: person icon → direct link to /profile/
│   ├── registration/
│   │   ├── login.html
│   │   └── logged_out.html
│   └── users/
│       ├── profile_view.html
│       └── profile_edit.html
└── static/
    └── (project-level static files if needed)
```

- **config**: Single Django project package (settings, root URLs, WSGI).
- **apps/users**: All profile and lease-officer–related code in one app. Include `apps.py` (AppConfig with `name = "apps.users"`), and a management command at `apps/users/management/commands/setup_initial_user.py`. Create the app inside `apps/` by either creating `apps/` and `apps/users/` (and `apps/users/migrations/`) manually, or running `python manage.py startapp users` then moving the app into `apps/users/` and fixing the `name` in `apps.py`.
- **Templates**: Centralized under `templates/` (add `'DIRS': [BASE_DIR / 'templates']` in `TEMPLATES` in settings). Use `registration/` and `users/` subdirs. Django finds templates in `DIRS` first.
- **URL names**: Include auth with `path('accounts/', include('django.contrib.auth.urls'))` (so login is at `/accounts/login/` and URL name `login`). In `apps/users/urls.py` set `app_name = 'users'` and use names `profile` and `profile_edit`; in templates use `{% url 'users:profile' %}` and `{% url 'users:profile_edit' %}`.

---

## 5. Data Model

### 5.1 User (Django built-in)

- Use `django.contrib.auth.models.User` (username, password, `is_staff`, etc.).
- No custom user model in v1 to keep the plan simple; profile is a OneToOne extension.

### 5.2 LeaseOfficerProfile (custom)

- **OneToOne** with `User` (one profile per user).
- **Fields**:
  - `user` (OneToOneField to User, related_name='lease_officer_profile')
  - `first_name` (CharField) — can mirror or override User.first_name
  - `last_name` (CharField) — can mirror or override User.last_name
  - `full_name` (CharField, optional or derived) — for display; can be a property or stored field
  - `phone_number` (CharField)
  - `email` (EmailField) — can mirror or override User.email
  - `timezone` (CharField) — IANA timezone name (e.g. America/New_York); default America/New_York. Used to display dates and times app-wide (deal dates, document version dates, etc.). Daylight saving is handled automatically by the timezone database.
- **Conventions**: Prefer one source of truth (e.g. profile) for display; optionally sync with `User` on save for consistency with admin/auth. Middleware activates the profile timezone per request so template date/time filters show the user's local time.

**Design choice**: Store `full_name` as a CharField (or computed property from first_name + last_name). Plan will assume a **computed property** in code and/or a `save()` that sets a `full_name` field from first + last to keep display logic simple.

---

## 6. Initial User and Data

- **Username**: `karl`
- **Password**: `karl` (plain for demo; document that production must use strong passwords and env-based secrets)
- **Profile**: First = "Karl", Last = "Matthews", Phone = "9197440153", Email = "kmatthews@signix.com", Timezone = America/New_York
- **Implementation**: Use a **management command** (e.g. `setup_initial_user`) that:
  - Creates user `karl` if not present (set `is_staff=True`, `is_superuser=True` for full admin access).
  - Creates/updates `LeaseOfficerProfile` with the above data.
- **Documentation**: Setup order is in this plan (Section 14): create and activate a venv first, then install dependencies, run migrations, and run the setup command.

---

## 7. Authentication and Menu

- **Root** (`/`): Redirect authenticated users to `/profile/`, others to `/accounts/login/`.
- **Login**: Django's `LoginView` at `/accounts/login/`; redirect after login to `/profile/`.
- **Logout**: Django's logout view; **must be POST** (a GET link causes 405). Use a form with `{% csrf_token %}` and a submit button styled as a nav link.
- **Menu (app pages)**: Custom sidebar in `base.html` (same layout style as Admin): Profile, Admin, Log out. Login and logged_out use `base_plain.html` (no sidebar).
- **Menu (Admin)**: Jazzmin `custom_links` in settings — **must be a dict** keyed by app label (e.g. `"main": [{"name": "Back to app", "url": "/profile/", "icon": "fas fa-arrow-left"}, ...]`), not a list. Adds "Back to app" and "Admin" in the Admin sidebar.
- Use `@login_required` on profile (and future) views.

---

## 8. Profile Flow

- **View** (`/profile/`): Display current user's profile (first name, last name, full name, phone, email, time zone). Read-only page with an "Edit" button.
- **Edit** (`/profile/edit/`): Form to update first name, last name, phone, email, and time zone. Full name can be read-only (computed) or editable per model design. On save, redirect to profile view and show a success message. The profile time zone controls how dates and times are displayed elsewhere in the app (e.g. deal dates, document version dates).
- **Permissions**: User can only view/edit their own profile (enforced in the view by using `request.user`).

---

## 9. Admin (Django Admin + Jazzmin)

- **Admin site**: Django Admin enabled; Jazzmin used as the admin theme.
- **Users**: Default Django "Users" and "Groups" from `django.contrib.auth`. Use a superuser (e.g. initial user with `is_superuser=True`) for add/edit/delete users.
- **LeaseOfficerProfile**: Not registered in admin in this plan (optional to add later).
- **Sidebar**: Jazzmin `custom_links` (dict format) provides "Back to app" → `/profile/` and "Admin" → `/admin/`.
- **Person icon (top-right in Admin)**: The default dropdown often does nothing (navigates to `#`). Override `templates/admin/base.html` (copy from Jazzmin, then replace the user dropdown `<li>` with a single link: `<a class="nav-link btn" href="/profile/" title="Profile">` with the same icon) so the person icon goes directly to the app profile page.

---

## 10. Configuration and Security (Minimal for Demo)

- **SECRET_KEY**: Load from environment variable in production; for local/demo, a default in settings is fine (document in this plan to override in production).
- **DEBUG**: Default True for demo; for production set `DEBUG=False` and configure `ALLOWED_HOSTS`.
- **SQLite**: Default `db.sqlite3` in project root; add to `.gitignore` if you do not want to commit the DB (optional).
- **Time zone**: Set `USE_TZ = True` so datetimes are stored in UTC. Set `TIME_ZONE` to the default display zone (e.g. America/New_York) for anonymous users and fallback; logged-in users' profile timezone overrides this per request via middleware.

---

## 11. Running and Debugging in Cursor

To run and debug the application from Cursor's Run/Debug UI (e.g. F5):

- **Launch configuration**: Add a `.vscode/launch.json` with a configuration that runs the Django development server (e.g. `python manage.py runserver` or the built-in "Django" debug type if available). This allows starting the app with breakpoints, the debug console, and stop/restart from the editor.
- **Working directory**: Set the launch config's `cwd` (or equivalent) to the project root (where `manage.py` lives) so Django finds settings and the app.
- **Python interpreter**: Use the project's virtual environment (e.g. `.venv`) for the debug session. This can be done by:
  - Selecting the venv as the Python interpreter in Cursor (status bar or Command Palette), and/or
  - Adding a `.vscode/settings.json` with `python.defaultInterpreterPath` pointing at the venv's Python (e.g. `${workspaceFolder}/.venv/bin/python`), so Run/Debug uses that environment by default.

No other plan changes are required; the app runs as usual under `runserver` when started via the debugger.

---

## 12. Code Quality and Conventions

- **Comments**: Docstrings for modules, classes, and non-trivial functions; short inline comments for non-obvious logic.
- **Organization**: One main responsibility per file (e.g. `views.py` for views, `forms.py` for forms, `urls.py` for URL routing).
- **Naming**: Clear names (e.g. `LeaseOfficerProfile`, `profile_view`, `profile_edit`); consistent URL names (`profile`, `profile_edit`). App display name on screen: **Vehicle Leasing** (Jazzmin `site_title` / `site_brand` / `site_header` and app base template brand).

---

## 12.1 Implementation notes: UI and navigation

These are the concrete steps that match the Admin look and fix common issues when building from scratch.

**App pages: left sidebar (match Admin)**

- Use a **custom base template** for app pages (Profile, etc.), not the top navbar only. Give it the same structure as Admin: fixed **left sidebar** (e.g. 250px, dark background `#343a40`) + **main content** area (e.g. light grey `#f4f6f9`), with a **content header** bar (page title) above the main content.
- Put navigation in the sidebar: brand link, then Profile, Admin, and Log out. Use a `content_header` block for the page title and a `content` block for the body.
- **Login and logged_out** should **not** use the sidebar (they are pre-auth). Use a second base, **`base_plain.html`**, with a simple centred card; have `login.html` and `logged_out.html` extend `base_plain.html`, and profile templates extend `base.html`.
- **Login error message (invalid credentials)**: Do **not** use `{{ form.non_field_errors }}` alone inside an alert — Django outputs a `<ul>`, which can render narrow and misaligned with the form. Instead loop over the errors in a full-width alert: `{% for error in form.non_field_errors %}<span class="d-block">{{ error }}</span>{% endfor %}` inside `<div class="alert alert-danger w-100 mb-3" role="alert">`, so the message matches the width of the username/password fields.

**Logout: POST and alignment**

- Django's logout view **only accepts POST**. A plain `<a href="{% url 'logout' %}">` causes **405 Method Not Allowed**. Use a **form** that POSTs to `{% url 'logout' %}` with `{% csrf_token %}` and a **submit button** styled to look like the other nav links (same padding, no border, e.g. `class="nav-link border-0 bg-transparent"` with `d-flex align-items-center` on the form so it aligns with Profile/Admin in the sidebar).

**Admin: Jazzmin menu and "Back to app"**

- In `JAZZMIN_SETTINGS`, **`custom_links` must be a dict** keyed by app label, not a list. A list causes a 500 (e.g. `"custom_links": {"main": [{"name": "Back to app", "url": "/profile/", "icon": "fas fa-arrow-left"}, {"name": "Admin", "url": "/admin/", "icon": "fas fa-cog"}]}`). This adds a "Back to app" link (and Admin) in the Admin **left** sidebar so users can return to the app without the browser back button.

**Admin: person icon (top-right)**

- The default Jazzmin user dropdown (person icon) often **does nothing** (click goes to `#`). Fix it by **overriding** the admin base template: create **`templates/admin/base.html`** in the project (copy the full file from Jazzmin's `templates/admin/base.html`), then find the `<li class="nav-item dropdown">` that contains the user icon and the dropdown menu. **Replace that whole `<li>...</li>`** with a single link: `<li class="nav-item"><a class="nav-link btn" href="/profile/" title="Profile"><i class="far fa-user" aria-hidden="true"></i></a></li>`. No dropdown; the icon goes straight to the app profile page.

**Display name**

- Use a short app name on screen (e.g. **Vehicle Leasing**). Set it in: (1) **Jazzmin** — `site_title`, `site_header`, and `site_brand` in `JAZZMIN_SETTINGS`; (2) **App base** — the sidebar brand link text in `base.html`; (3) **Page titles** — default `{% block title %}` in base templates and any `content_header` or title blocks in child templates.

**Common errors: 500 and 405**

- **500 when opening Admin** (`/admin/`): Usually caused by **`custom_links`** being a **list** in `JAZZMIN_SETTINGS`. Jazzmin expects a **dict** keyed by app label (e.g. `"main": [list of links]`). Using a list leads to `AttributeError` (e.g. `.items()` on a list) and a 500. Fix: set `custom_links` to a dict as in the "Admin: Jazzmin menu" note above.
- **405 when clicking Log out**: Django's logout view does not allow GET. A normal link to the logout URL returns **405 Method Not Allowed**. Fix: use a **POST form** with `{% csrf_token %}` and a submit button (see "Logout: POST and alignment" above).

---

## 13. Implementation Order (Checklist)

1. **Virtual environment (first step for integration/setup)**
   - Create a virtual environment using Python's built-in `venv` (e.g. `python -m venv .venv`).
   - Activate it (e.g. `.venv/bin/activate` on Linux/macOS, `.venv\Scripts\activate` on Windows).
   - All subsequent steps (install, migrate, runserver) assume this venv is active so dependencies are isolated.

2. **Project bootstrap**
   - Create Django project (`config`) and `requirements.txt` (Django, Jazzmin, etc.).
   - Add `.gitignore` (Python, venv, `db.sqlite3`, `__pycache__`, `.env`, etc.).
   - Configure `config/settings.py`: Put **Jazzmin first** in `INSTALLED_APPS` (so it overrides admin templates), then `django.contrib.*`, then `apps.users`. Set `TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']`. Set SQLite, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, and `JAZZMIN_SETTINGS` (including `custom_links` as a **dict**; see Section 12.1).
   - Add `.vscode/launch.json` with a configuration that runs Django (e.g. `"module": "django"`, `"args": ["runserver", "8000"]`, `"cwd": "${workspaceFolder}"`, `"env": {"DJANGO_SETTINGS_MODULE": "config.settings"}`). Optionally add `.vscode/settings.json` with `"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"` so Run/Debug uses the project venv.

3. **Users app and model**
   - Create the `apps/users` app (ensure `apps/` package and `apps/users/` package exist; add `apps/users/apps.py` with `name = "apps.users"`, and `apps/users/migrations/__init__.py`). Add `apps.users` to `INSTALLED_APPS`.
   - Define `LeaseOfficerProfile` with OneToOne to User and fields above; add `full_name` as a computed property (e.g. `@property` from first_name + last_name) and `timezone` (CharField, IANA name, default America/New_York, choices for common zones).
   - Run `python manage.py makemigrations users` and `python manage.py migrate`.
   - Add middleware (e.g. in `apps/users/middleware.py`) that activates the request user's profile timezone for each request so that all date/time display in templates uses the user's local time; register it in `MIDDLEWARE` after `AuthenticationMiddleware`. Set `TIME_ZONE` in settings to the default display zone (e.g. America/New_York) for anonymous or fallback.

4. **Initial user**
   - Add a management command at `apps/users/management/commands/setup_initial_user.py` that creates or updates user `karl` (password `karl`, `is_staff=True`, `is_superuser=True`) and a `LeaseOfficerProfile` with the plan data (Section 6), including timezone America/New_York. Use `get_or_create` so the command is idempotent.

5. **Auth and base template**
   - Configure `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`.
   - Add `templates/base.html` with **left sidebar layout** (match Admin), content header block, and messages; add `templates/base_plain.html` for login/logged_out (no sidebar). See **Section 12.1** for layout and logout (POST form, alignment).
   - Add `registration/login.html` and `logged_out.html` (extend `base_plain.html`). In the login template include `<input type="hidden" name="next" value="{{ next }}">` so redirect-after-login works. Profile templates extend `base.html`. Use **Bootstrap 5** (and optionally Bootstrap Icons) in the app base templates so the sidebar and content match a modern layout; login error message: see Section 12.1 (full-width alert, loop over `form.non_field_errors`).

6. **Profile views and URLs**
   - Implement a root redirect view (e.g. `root_redirect`: if authenticated → redirect to `users:profile`, else → redirect to `login`). Implement profile view and profile edit view; use `@login_required` and `get_object_or_404(LeaseOfficerProfile, user=request.user)`.
   - Add `forms.py` with a ModelForm for the profile (fields: first_name, last_name, phone_number, email, timezone); on valid POST save and redirect to profile with a success message.
   - In `config/urls.py`: `path("", root_redirect)`, `path("accounts/", include("django.contrib.auth.urls"))`, `path("", include("apps.users.urls"))`, `path("admin/", admin.site.urls)`. In `apps/users/urls.py` set `app_name = "users"` and define `path("profile/", profile_view, name="profile")`, `path("profile/edit/", profile_edit, name="profile_edit")`.
   - Override `templates/admin/base.html` so the Admin top-right person icon is a direct link to `/profile/` (see Section 9 and Section 12.1).

*(Optional later: register `LeaseOfficerProfile` in admin; add a separate README.)*

---

## 14. Implementation Batches and Verification

Implementation can be done in **two batches**. After each batch, run the verification steps below.

### Batch 1 — Foundation (steps 1–4)

**Includes:** Virtual environment, project bootstrap (Django project, settings, `.vscode`, `.gitignore`), users app and `LeaseOfficerProfile` model, migrations, and initial-user setup command.

**How to test after Batch 1:**

1. **Venv:** Activate the venv. Run `which python` (Linux/macOS) or `where python` (Windows) and confirm the path is inside `.venv`.
2. **Django:** With venv active, run `pip install -r requirements.txt`, then from the project root run `python manage.py check` — you should see "System check identified no issues (0)." Optionally start the server (F5 or `python manage.py runserver`) and confirm it starts without errors (a default or 404 page is fine until Batch 2).
3. **Migrations:** Run `python manage.py migrate`. Confirm migrations for `users` (and auth/sessions) are applied without errors.
4. **Initial user:** Run the setup command (e.g. `python manage.py setup_initial_user`). Then in the shell verify:
   - `python manage.py shell`
   - `from django.contrib.auth.models import User; from apps.users.models import LeaseOfficerProfile`
   - `u = User.objects.get(username='karl')`
   - `u.lease_officer_profile.first_name` → `'Karl'`, `u.lease_officer_profile.email` → `'kmatthews@signix.com'`, `u.lease_officer_profile.phone_number` → `'9197440153'`, `u.lease_officer_profile.timezone` → `'America/New_York'`

You will not have the login page or Profile menu until Batch 2; Batch 1 is complete when the above all pass.

### Setup and run (from scratch)

1. **Create and activate a virtual environment** (project root):  
   `python3 -m venv .venv` then `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows).
2. **Install:** `pip install -r requirements.txt`
3. **Migrations:** `python manage.py migrate`
4. **Initial user:** `python manage.py setup_initial_user` (creates `karl` / `karl`, superuser).
5. **Run:** `python manage.py runserver` or Cursor Run/Debug (F5) with "Django: runserver". Open e.g. `http://127.0.0.1:8000/`, log in with **karl** / **karl**. Use **Profile** and **Admin** from the menu. App display name used on screen: **Vehicle Leasing**.

### Batch 2 — Auth and profile (steps 5–6)

**Includes:** Login/logout URLs and redirects, base template, login template, Jazzmin menu (Profile, Admin), profile view and edit views, forms, and URL wiring.

**How to test after Batch 2:**

1. Start the server (F5 or `python manage.py runserver`). Open the app in the browser (e.g. `http://127.0.0.1:8000/`).
2. You should be redirected to the login page. Log in with username `karl`, password `karl`.
3. After login you should see the app with a menu. Open **Profile** — the profile view should show Karl's name, email, phone, and time zone. Use **Edit** to change a field (including time zone), save, and confirm the profile view shows the update. Dates and times shown elsewhere in the app (e.g. deal dates, document version dates) will use the profile time zone.
4. Use the menu to open **Admin** (or go to `/admin/`); confirm the Django admin loads (log in with karl/karl if prompted). Click "Back to app" in the sidebar to return; click the person icon in the top-right to go to Profile.
5. **Logout:** Use Log out in the app menu (or in Admin); confirm no 405 (logout must be POST).

---

## 15. Out of Scope (Initial Version)

- SIGNiX integration (planned for a later phase).
- Lease-specific models (e.g. jet pack lease documents, lessees); can be added when moving toward signing.
- Custom user model (optional future refactor if needed).
- Production deployment (e.g. Gunicorn, env-based config).
- Registering `LeaseOfficerProfile` in Django admin (optional; Users/Groups remain available).
- A separate README (setup and run are in this plan, Section 14).

---

## 16. Review and Next Steps

- This plan reflects what was implemented: steps 1–6, in two batches, with the implementation notes above (logout POST, Jazzmin custom_links dict, Admin person-icon override, sidebar layout, "Vehicle Leasing" display name, superuser for initial user).
- Use **Section 13** as the implementation checklist and **Section 14** for batches and setup/run when creating similar applications from scratch.
