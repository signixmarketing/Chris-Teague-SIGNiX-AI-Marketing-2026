# Knowledge: File Upload, Storage, and Media (Without a Document Management Subsystem)

This document describes the **pattern** of uploading files (e.g. images), storing them with metadata, and exposing **stable URLs** for reference—**without** introducing a full document management subsystem (DMS). It is reusable for document-centric applications that need logos, diagrams, or other assets in templates. This project implements this pattern for **Images** (PLAN-ADD-IMAGES); the design is in [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md).

**When to use a DMS:** If you need versioning, complex access control, or integration with an external system (e.g. Directus, S3 + metadata API), you may add or replace this layer with a dedicated DMS. The knowledge here applies to the **simple** case: app-managed storage under a media root, with a single source of truth in your application.

---

## 1. The Pattern in Plain Language

1. **Upload** — Users (or admins) upload files through the application UI (e.g. image upload form).
2. **Store** — The application stores the file on disk (or object storage) under a configured media root and stores **metadata** (e.g. name, path, unique id) in the database.
3. **Expose URL** — Each stored file has a **stable URL** (e.g. `/media/images/<id>/filename.png` or `/media/images/<uuid>.png`) so templates, document generation, or other features can reference it by URL or by a stable identifier (e.g. UUID).
4. **Replace** — When the user uploads a **replacement** file (e.g. new logo), the same record can point to the new file. If the URL is **stable** (e.g. includes id or uuid in the path), existing references (e.g. in document templates) keep working without change.

No document management layer is required: no version history of the file, no workflow states, no separate "document" entity—just **file + metadata + URL**.

---

## 2. Why Stable URLs Matter

Document templates (e.g. HTML with `<img src="...">`) and mapping configurations (e.g. "image variable → image:<uuid>") reference assets by URL or by identifier. If the user **replaces** an image (e.g. updated logo), two approaches:

- **Unstable URL** — Each upload gets a new path (e.g. `media/images/logo_abc123.png` → `media/images/logo_def456.png`). References in saved templates break unless you rewrite them on replace.
- **Stable URL** — The path includes a **stable** part (e.g. `media/images/<id>/image` or `media/images/<uuid>.png`) so the same record always serves from the same URL. Replacing the file updates the file on disk but the URL stays the same; templates keep working.

This project uses a **stable URL** strategy (e.g. `upload_to` that includes the instance id or a uuid) so that replacement does not break template references. See [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) and [03-IMAGES/10-PLAN-ADD-IMAGES.md](../03-IMAGES/10-PLAN-ADD-IMAGES.md).

---

## 3. Django Conventions (MEDIA_ROOT, MEDIA_URL, ImageField)

- **MEDIA_ROOT** — Directory on disk where uploaded files are stored (e.g. `BASE_DIR / "media"`). Not served by Django in production (use the web server or a CDN); in **development**, serve with `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` in the main `urls.py`.
- **MEDIA_URL** — URL prefix for media files (e.g. `"/media/"`). So the full URL for a file might be `request.build_absolute_uri(instance.file.url)` → `http://localhost:8000/media/images/...`.
- **ImageField / FileField** — Store the file; `upload_to` controls the path under MEDIA_ROOT. Use a **callable** or path that includes `id` or `uuid` for stability when the file is replaced (e.g. `upload_to=lambda i, fn: f"images/{i.id}/{fn}"` or `upload_to="images"` with a custom name that includes uuid).
- **Pillow** — Required for ImageField (Django dependency). Install via `pip install Pillow` or `requirements.txt`.
- **Deletion** — Override `Model.delete()` to remove the file from disk when the record is deleted, or accept orphaned files and clean up later. PLAN-ADD-IMAGES leaves this as an implementation choice.

---

## 4. When to Use a Document Management Subsystem

The pattern above is sufficient when:

- You have a **single** logical version of each asset (e.g. "the current logo").
- Access control is **application-level** (e.g. authenticated users only; no per-file permissions).
- You do **not** need audit trails, version history, or approval workflows for the file itself.

Consider a **DMS** (e.g. Directus, custom S3 + metadata, or a document management API) when:

- You need **versioning** (keep history of file changes) or **approval workflows**.
- You need **fine-grained permissions** per file or folder.
- You want to **offload** storage and serving to an external system (e.g. S3, Directus assets).
- You have **many** asset types or complex metadata beyond name and file.

**Extending this project:** The current design (DESIGN-IMAGES) uses app-managed storage and a stable identifier (e.g. uuid) for resolution. To integrate Directus (or similar), you would: (1) keep the **contract** that document features resolve "image:<uuid>" (or a URL) to an HTTP-accessible image URL; (2) replace the resolution implementation (e.g. `Image.objects.get(uuid=...)` → Directus API or asset URL builder). The mapping UI and context builder would still work; only the **source** of the file and URL would change. See [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) for the extension point.

---

## 5. References in This Repo

| Document | Content |
|----------|---------|
| [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) | This application’s design: Image model, stable URLs, how document features consume images, extension point for DMS. |
| [03-IMAGES/10-PLAN-ADD-IMAGES.md](../03-IMAGES/10-PLAN-ADD-IMAGES.md) | Implementation: apps.images, model, MEDIA config, CRUD, list with URL column, edit with replacement. |
| [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) | Image variables in dynamic templates; mapping optgroup; `image:<uuid>`; context builder resolution. |
| [KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md](KNOWLEDGE-DOCUMENT-CENTRIC-APPS.md) | General pattern; document generation enablers include file/assets (images). |

---

*This knowledge file describes the **pattern** of file upload and media storage without a DMS. For this application’s design and implementation, see [03-IMAGES/DESIGN-IMAGES.md](../03-IMAGES/DESIGN-IMAGES.md) and [03-IMAGES/10-PLAN-ADD-IMAGES.md](../03-IMAGES/10-PLAN-ADD-IMAGES.md).*
