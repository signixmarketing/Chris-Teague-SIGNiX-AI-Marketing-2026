# Plan: Add Images to the Lease App

This document outlines how to add an **Images** feature to the Django lease application. Users can upload images (e.g. for use in document templates); each image has a user-provided name and is stored under `media/images/`. The list page shows a table with a **relative URL** column for use in templates; the edit page shows the current image, the URL as read-only, and allows uploading a replacement.

**Review this plan before implementation.** Implementation order is in **Section 6**; **Section 6a** defines two batches and how to test each one.

---

## 1. Goals and Scope

- **Model**: An `Image` (or `DocumentImage`) model with a user-provided **name** (filename/label) and an **ImageField** for the uploaded file. Files are stored under `media/images/` (generic folder, not lease-specific).
- **Data**: No seed data; the Images table starts **empty**.
- **UI**: An **Images** page (table of images). Columns: Name, **URL** (relative path to use when referencing the image in a template), optional preview thumbnail, and Actions (Edit, Delete). Add image: provide name and upload file. Edit image: show current image, show URL as **non-editable**, and allow uploading a **replacement** image.
- **Access**: Authenticated users only (`@login_required`). Any logged-in user can manage images.

---

## 2. Image Model and Storage

- **Persistence**: Image metadata (name, file path) is stored in the project’s **SQLite** database. The actual file is stored on disk under **MEDIA_ROOT** in the subfolder **images/** (so the path is `media/images/` relative to the project, or whatever MEDIA_ROOT is set to).
- **App**: New app `apps.images` (under `apps/`), with `name = "apps.images"` in `AppConfig`.
- **Model**: `Image` (or `DocumentImage`)
  - `name` — `CharField` (e.g. max_length=255). User-provided filename/label for the image (e.g. "Lease logo", "company_logo.png").
  - `file` — `ImageField` with `upload_to="images"` (or a callable that includes the instance id for a stable URL—see note below) so uploaded files are stored under `MEDIA_ROOT/images/`. Use a unique filename; if the path includes the image id, the URL will not change when the user uploads a replacement.

**URL for templates**: The **relative URL** to reference the image in a template is the value of `image.file.url` (e.g. `/media/images/logo_abc123.png`). This is what the app will serve when the browser or document engine requests it—the response is the raw image (no HTML). Display this URL in the list table and on the Edit page as a **copyable** read-only field (e.g. a read-only `<input>` so the user can select-all and copy) for pasting into document templates (e.g. `<img src="/media/images/…">`).

**Stable URL when replacing**: If the user uploads a replacement image, the default `upload_to` may generate a new filename, which would change the URL and break any template that already references it. For easier use in templates, consider an `upload_to` that keeps the URL stable when the file is replaced—e.g. a path that includes the image id (e.g. `images/%(id)s/` or similar) so the same record always serves from the same URL.

**Conventions**: Docstrings, `__str__` (e.g. return `name`). `verbose_name` / `verbose_name_plural` in `Meta`. Configure **MEDIA_ROOT** and **MEDIA_URL** in settings; in development, serve media files via `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` in the main `urls.py` so the relative URL is reachable.

---

## 3. No Seed Data

The Images list starts empty. No management command or fixture is required. Users add images via the UI.

---

## 4. Pages and Behavior

### 4.1 List page (Images table)

- **URL**: `/images/` (e.g. name `image_list`).
- **Content**: A table with columns **Name**, **URL** (the relative URL from `image.file.url`—e.g. `/media/images/…`—so the user can copy it for use in a template), optional **Preview** (small thumbnail if desired), and **Actions** (Edit, Delete per row).
- **Header**: Page title "Images"; primary button **Add image** linking to `/images/add/`.
- **Empty state**: If there are no images, show the table with a message like "No images yet. Add one to get started." Do **not** add a second "Add image" button below the table—the header button is sufficient.
- **Layout**: Use `base.html`. Add an **Images** link in the sidebar (e.g. after Deals or in a logical place before Admin).

### 4.2 Add image

- **URL**: `/images/add/` (name `image_add`).
- **Method**: GET shows form; POST creates an image record and stores the uploaded file; redirect to list with "Image added."
- **Form**: Fields **name** (text, user-provided filename/label) and **file** (file upload, image types). Enctype `multipart/form-data`. Validation: name required; file required and must be an image type. On save, file is stored under `media/images/` (via `upload_to="images"`).

### 4.3 Edit image

- **URL**: `/images/<id>/edit/` (e.g. `image_edit` with `pk`).
- **Method**: GET shows the edit form; POST updates the record and optionally replaces the file.
- **Display**:
  - **URL**: Show the relative URL (`image.file.url`) as a **non-editable** field (e.g. read-only text input or plain text) so the user can copy it for use in templates.
  - **Current image**: Once an image is uploaded, **show the image** on the Edit page (e.g. `<img src="{{ image.file.url }}" />` or thumbnail).
  - **Replacement**: Allow the user to **upload a replacement image** (file input). If a new file is provided on POST, replace the existing file (save new file, optionally delete old file from disk to avoid orphaned files); if no new file is provided, keep the existing file. Name can be edited.
- **Form**: Name (editable); file (optional on edit—only required when adding). If file is left blank on edit, keep current file.

### 4.4 Delete image

- **Requirement**: Deletion must use **POST** (not GET). **Dedicated confirmation page**: GET `/images/<id>/delete/` shows "Are you sure you want to delete this image?" (with image name and optional thumbnail); form POSTs; on POST, delete the record and remove the file from disk (or rely on model’s delete to clean up), then redirect to list with "Image deleted."

---

## 5. Navigation and Integration

- **Sidebar** (`templates/base.html`): Add an **Images** link (e.g. after Deals, before Admin): Text "Images", URL `{% url 'images:image_list' %}`, icon e.g. `bi bi-image`. Mark active when `request.resolver_match.app_name == 'images'`.
- **Config**: In `config/urls.py`, add `path("images/", include("apps.images.urls"))`. In `config/settings.py`, add `"apps.images"` to `INSTALLED_APPS`. Configure **MEDIA_ROOT** (e.g. `BASE_DIR / "media"`) and **MEDIA_URL** (e.g. `"/media/"`). In development, append `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` so the app serves uploaded files at the relative URL.
- **Jazzmin**: Optional: add "Images" custom link in the Admin sidebar to `/images/`.

---

## 6. Implementation Order (Checklist)

### Batch 1 — Data layer and media (steps 1–3)

1. **Create `apps.images` app**
   - Create `apps/images/` with `__init__.py`, `apps.py` (`name = "apps.images"`), `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, and `migrations/__init__.py`.
   - Add `"apps.images"` to `INSTALLED_APPS` in `config/settings.py`.

2. **Media configuration**
   - In `config/settings.py`, set **MEDIA_ROOT** (e.g. `BASE_DIR / "media"`) and **MEDIA_URL** (e.g. `"/media/"`). Ensure `media/` is in `.gitignore` if you do not want to commit uploaded files.
   - In `config/urls.py`, in development, add serving of media files: `from django.conf import settings` and `from django.conf.urls.static import static`, then `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` (often guarded by `if settings.DEBUG`).

3. **Image model**
   - In `apps/images/models.py`, define `Image` with `name` (CharField) and `file` (ImageField, `upload_to="images"`). Add `__str__` (return name) and `Meta` verbose names. Optionally override `delete()` to remove the file from disk when the record is deleted, or use Django’s default behavior (file may remain; can be cleaned up in a later phase).
   - Run `python manage.py makemigrations images` and `python manage.py migrate`. Ensure the `media/images/` directory is created on first upload (Django creates `upload_to` directories as needed).

No seed data. Batch 1 is complete when the app is installed, media is configured, the model exists, and migrations are applied.

### Batch 2 — UI and CRUD (steps 4–9)

4. **Forms**
   - In `apps/images/forms.py`, create an `ImageForm` (ModelForm) with fields `name` and `file`. On edit, make `file` **optional** (required=False when instance is provided) so the user can leave it blank to keep the current image. Use `enctype="multipart/form-data"` on the form tag in the template.

5. **Views**
   - List: `image_list` — list all images; pass `image_list` to template. Each image’s URL for the table is `image.file.url` (relative).
   - Add: `image_add` — GET form; POST create with `request.FILES`; save and redirect to list with "Image added."
   - Edit: `image_edit` — GET form with instance (current name and no new file); POST update name and, if a new file was uploaded, replace the file. Show the current image and the read-only URL in the template.
   - Delete: `image_delete_confirm` — GET confirmation page (show image name and optionally thumbnail); POST delete image and redirect to list with "Image deleted." All views `@login_required`.

6. **URLs**
   - In `apps/images/urls.py`: `app_name = "images"`; routes for list (`""`), add (`"add/"`), edit (`"<int:pk>/edit/"`), delete (`"<int:pk>/delete/"`).
   - In `config/urls.py`: `path("images/", include("apps.images.urls"))`.

7. **Templates**
   - `templates/images/image_list.html` — table with Name, URL (relative), optional Preview, Actions; single "Add image" button in the header only (no duplicate below the table when empty); empty state message in table body when no images.
   - `templates/images/image_form.html` — add form: name + file upload. Edit form: name, read-only URL (display `image.file.url`), display current image (`<img src="{{ image.file.url }}" />`), and file input for replacement (optional).
   - `templates/images/image_confirm_delete.html` — confirmation message and POST form (Cancel → list, Delete → submit).

8. **Sidebar**
   - Update `templates/base.html`: add Images nav item with link to `images:image_list` and active state when on images app.

9. **Optional**
   - Register `Image` in Django admin (list_display: name, URL or file preview, etc.). Add Jazzmin `custom_links` entry for "Images" → `/images/`.

10. **Verification**
    - Run server; log in; open Images (empty list); add an image (name + file); list shows name and relative URL; edit shows image and read-only URL, upload replacement and confirm it updates; delete via confirmation page (POST only). Confirm the relative URL is reachable in the browser (raw image, no HTML).

---

## 6a. Implementation Batches and Verification

Implement in **two batches**. After each batch, run the verification steps below.

### Batch 1 — Data layer and media (steps 1–3)

**Includes:** Create `apps.images` app, add to `INSTALLED_APPS`, configure MEDIA_ROOT and MEDIA_URL and serve media in development, define `Image` model, run migrations.

**How to test after Batch 1:**

1. **Django check:** With venv active, run `python manage.py check`. Expect "System check identified no issues (0)."
2. **Migrations:** Run `python manage.py migrate`. Confirm the `images` migration is applied (e.g. `images_image` table exists).
3. **Media config:** Ensure `MEDIA_ROOT` and `MEDIA_URL` are set and that `urlpatterns` in development include `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`. Place a test file in `media/images/test.png` (or create the directory and file manually) and open `http://127.0.0.1:8000/media/images/test.png` in the browser; you should see the image (raw, no HTML). Remove test file if desired.

You will not have the Images page or sidebar link until Batch 2. Batch 1 is complete when the above pass.

### Batch 2 — UI and CRUD (steps 4–10)

**Includes:** Forms (with file upload; file optional on edit), views (handle multipart POST), URLs, templates (list with URL column, form with read-only URL and current image on edit, replace file, confirm delete), sidebar, optional admin/Jazzmin.

**How to test after Batch 2:**

1. Start the server. Log in as **karl** / **karl**.
2. **Sidebar:** **Images** appears. Click it; list at `/images/` (empty).
3. **Empty state:** Table shows "No images yet. Add one to get started."; the only "Add image" button is in the page header (no second button below the table).
4. **Add:** Click "Add image", enter a name and choose an image file; submit. Redirect to list with "Image added." and one row: Name, relative URL (e.g. `/media/images/…`), Edit, Delete.
5. **URL column:** Copy the URL from the table; open it in the browser. The response should be the raw image (no HTML).
6. **Edit:** Click Edit. Page shows name (editable), **read-only URL** (same as in table), and the **current image** displayed. Change the name or upload a replacement file; save. List and edit page reflect the update; if replaced, the URL may change (new filename) or stay the same depending on upload_to implementation.
7. **Edit without new file:** Edit again, change only the name, leave file input empty; save. Image file should be unchanged; name updated.
8. **Delete:** Click Delete → confirmation page (GET). Submit delete form (POST). Image removed from list and "Image deleted." shown. Visiting delete URL with GET only does not delete.

Batch 2 is complete when all of the above pass.

---

## 7. File and URL Summary

| Item   | Value |
|--------|--------|
| App    | `apps.images` |
| Model  | `Image(name, file)` with `file` stored under `media/images/` |
| List   | `/images/` — table (Name, URL, optional Preview, Actions), Add button, empty state |
| Add    | `/images/add/` — form (name + file upload), redirect to list |
| Edit   | `/images/<id>/edit/` — form (name, read-only URL, current image, optional replacement file), redirect to list |
| Delete | GET `/images/<id>/delete/` — confirm; POST — delete, redirect to list |
| Nav    | Sidebar: "Images" → `/images/` |
| Media  | MEDIA_ROOT (e.g. `media/`), MEDIA_URL `/media/`, files under `media/images/` |
| Seed   | None; list starts empty |

---

## 8. Out of Scope (This Phase)

- Linking images to specific document types or templates (e.g. "lease logo"); that can be added later (e.g. by slug or FK).
- Image resizing, thumbnails, or format conversion.
- Pagination or search on the images list.
- Soft delete (hard delete only).

---

*End of plan. Proceed to implementation only after review.*
