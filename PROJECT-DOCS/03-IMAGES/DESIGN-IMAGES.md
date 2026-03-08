# Design: Images (File Assets for Document Generation)

This document captures the design for **image** (file asset) upload, storage, and exposure in the lease application. Images are used in document templates (e.g. logos, diagrams); they are stored by the application under a media root and referenced by a **stable URL** or **stable identifier** (e.g. UUID) so that template references survive file replacement. Implementation follows **10-PLAN-ADD-IMAGES.md**.

**Related designs:** **../06-DOCS/DESIGN-DOCS.md** defines how dynamic document templates consume images (image variables, mapping optgroup, `image:<uuid>`, context builder resolution). **../04-DATA-INTERFACE/DESIGN-DATA-INTERFACE.md** defines deal data; images are a **separate** source for the mapping UI (Images optgroup), not part of the deal-centric schema.

**Knowledge:** **../GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md** describes the general pattern of file upload and storage without a document management subsystem, stable URLs, and when to use a DMS. This design implements that pattern for images.

---

## Scope

- **Image entity** — Model with name (user-provided label) and file (uploaded image); storage under MEDIA_ROOT; stable URL or identifier for reference in templates.
- **UI** — List (table with Name, URL, Actions), Add, Edit (with current image and optional replacement), Delete with confirmation. No seed data; list starts empty.
- **Consumption by document features** — Dynamic templates can reference images via a stable identifier (e.g. `image:<uuid>`); the mapping UI offers an Images optgroup; the context builder resolves the identifier to an HTTP-accessible URL for rendering and for HTML-to-PDF.

This design does **not** cover document templates, document sets, or signing; those are in DESIGN-DOCS and related PLAN files. It does **not** introduce a full document management subsystem (versioning, workflow, external DMS); see Knowledge for when to add one.

---

## Current Platform (Assumed)

This design assumes **../01-BASELINE/10-PLAN-BASELINE.md** and **../02-BIZ-DOMAIN/PHASE-PLANS-BIZ-DOMAIN.md** (Vehicles, Contacts, Deals) are implemented:

- Django project, users app, auth, base templates.
- Business domain (apps.vehicles, apps.contacts, apps.deals) with standard CRUD and sidebar.

The Images plan adds **apps.images** and configures MEDIA_ROOT/MEDIA_URL. It does not replace baseline or biz domain.

---

## 1. Image Model and Storage

- **App:** `apps.images` (under `apps/`), `name = "apps.images"` in AppConfig.
- **Model:** `Image` (or `DocumentImage`)
  - `name` — CharField; user-provided filename/label (e.g. "Lease logo", "company_logo.png").
  - `file` — ImageField with `upload_to` such that the path is **stable** when the file is replaced (e.g. path includes instance id or uuid so the same record always serves from the same URL). Stored under MEDIA_ROOT (e.g. `media/images/`).
- **Conventions:** Docstrings, `__str__` (return name), verbose_name in Meta. Pillow required for ImageField.
- **MEDIA_ROOT / MEDIA_URL:** Configured in settings (e.g. MEDIA_ROOT = BASE_DIR / "media", MEDIA_URL = "/media/"). In development, serve media via `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` in the main urls.py so the relative URL (e.g. `/media/images/...`) is reachable.

Full field specs and upload_to behavior are in 10-PLAN-ADD-IMAGES.md.

---

## 2. Stable URL and Identifier

- **URL for templates:** The value of `image.file.url` (e.g. `/media/images/...`) is the relative URL to use in templates (e.g. `<img src="{{ ... }}">`). Display this URL in the list table and on the Edit page as a **copyable** read-only field so users can paste it into document templates.
- **Stable URL on replacement:** If the user uploads a replacement image, the URL must not change for existing references. Use an `upload_to` that includes a stable part (e.g. instance id or uuid) so the same record always serves from the same path. PLAN-ADD-IMAGES specifies the exact strategy (e.g. uuid in path).
- **Stable identifier for mapping:** Document features (DESIGN-DOCS) reference images by a stable identifier, e.g. `image:<uuid>`. The Image model may expose a UUID field (or use pk) so that the mapping configuration stores `image:<uuid>` and the context builder resolves it to the Image's file URL at render time. This allows templates to refer to "an image" without hard-coding the URL; when the file is replaced, the uuid stays the same and the resolved URL still points to the current file.

---

## 3. How Document Features Consume Images

- **Mapping UI:** The Dynamic Template mapping UI obtains deal-data paths from `get_paths_grouped_for_mapping()` (DESIGN-DATA-INTERFACE). It also appends an **Images** optgroup populated from the Image model—each image is offered as a source option with format `image:<uuid>` (or equivalent) and display name. Variables that are detected as "image" type (e.g. names ending in `_image_url`, `_logo_url`) are mapped to this optgroup. See DESIGN-DOCS.
- **Context builder:** At render time, the context builder resolves each image variable: for source `image:<uuid>`, it looks up the Image by uuid, obtains the file URL, and supplies an **absolute** URL (e.g. `request.build_absolute_uri(image.file.url)`) so that HTML-to-PDF (wkhtmltopdf) can load the image. See KNOWLEDGE-HTML-TO-PDF and DESIGN-DOCS.
- **No circumvention:** Deal data comes from `get_deal_data(deal)` only; image data comes from the Image model (or the resolution layer). The mapping UI and context builder use these designated sources; they do not traverse arbitrary models for deal or image data.

---

## 4. UI Conventions

- **Access:** Authenticated users only (`@login_required`). No per-image permissions in v1.
- **List:** Table with columns Name, URL (relative, copyable), optional Preview, Actions (Edit, Delete). Single "Add image" button in header only; no duplicate below the table when empty. Empty state message in table body when no images.
- **Add:** Form with name and file upload; multipart/form-data; redirect to list on success.
- **Edit:** Show current image, read-only URL, editable name, optional file input for replacement. If no new file on POST, keep existing file.
- **Delete:** Dedicated confirmation page (GET); POST performs delete. Optionally remove file from disk on delete (implementation choice in PLAN-ADD-IMAGES).
- **Sidebar:** "Images" link (e.g. after Deals, before Admin). Use base.html; consistent with other entities.

---

## 5. Extension Point: Document Management Subsystem

The current design uses **app-managed storage**: files under MEDIA_ROOT, metadata in the Image model, resolution via `Image.objects.get(uuid=...)` (or pk) to obtain the URL. This is sufficient for a single logical version per image and application-level access control.

**Future extension:** To integrate a **document management subsystem** (e.g. Directus, S3 + metadata API):

- **Contract to preserve:** Document features expect to resolve an image reference (e.g. `image:<uuid>`) to an HTTP-accessible URL. The mapping UI expects a list of image options (identifier + display name). The context builder expects a function that, given an identifier, returns the URL.
- **What to replace:** The **resolution layer**—instead of `Image.objects.get(uuid=...)` and `image.file.url`, the application would call the DMS API or URL builder to get the asset URL. The Image model (and PLAN-ADD-IMAGES UI) could be replaced by a DMS-backed "assets" list and resolution service, or the existing model could be retained and the DMS used only for certain asset types. DESIGN-DOCS and the context builder would continue to call "resolve image reference to URL"; only the implementation of that resolution would change.

See KNOWLEDGE-FILE-ASSETS-MEDIA for when to use a DMS and how this pattern fits.

---

## 6. Implementation Order and References

- **Implementation:** **10-PLAN-ADD-IMAGES.md** — Batch 1 (app, media config, model, migrations), Batch 2 (forms, views, URLs, templates, sidebar, optional admin). Section 6 and Section 6a for order and verification.
- **70-PLAN-MASTER.md:** Images is plan 3 in the main sequence (after Biz Domain Master, before Data Interface). Document features (PHASE-PLANS-DOCS) assume Images and Data Interface are in place.

---

## Decisions Log

### App-managed storage (no DMS in v1)

Images are stored under MEDIA_ROOT with metadata in the Image model. No versioning, no external DMS. Sufficient for logos and diagrams referenced in templates; keeps the stack simple. KNOWLEDGE-FILE-ASSETS-MEDIA describes when to add a DMS.

### Stable URL and stable identifier

URLs and references use a stable part (id or uuid) so that replacing the file does not break template or mapping references. Same record, same URL/identifier; only the file content changes.

### Images as separate source from deal data

Deal data comes from `get_deal_data(deal)`; images come from the Image model and are offered in a separate Images optgroup in the mapping UI. The context builder resolves `image:<uuid>` via the Image model (or future DMS). This keeps the deal-centric schema clean and allows images to be reused across deals and templates.

### Absolute URLs for HTML-to-PDF

When building the template context for document generation, image URLs are supplied as **absolute** URLs (e.g. `request.build_absolute_uri(image.file.url)`) so that wkhtmltopdf can load them. See KNOWLEDGE-HTML-TO-PDF and DESIGN-DOCS.

---

*End of design. Implementation follows 10-PLAN-ADD-IMAGES.md. See ../06-DOCS/DESIGN-DOCS.md for image variables and mapping; ../GENERAL-KNOWLEDGE/KNOWLEDGE-FILE-ASSETS-MEDIA.md for the file-asset pattern.*
