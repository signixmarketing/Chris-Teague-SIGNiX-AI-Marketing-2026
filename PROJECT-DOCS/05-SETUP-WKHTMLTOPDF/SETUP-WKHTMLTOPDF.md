# Setup: wkhtmltopdf for Dynamic Document Generation

This document is a **step-by-step setup guide** so that the Django app can convert rendered HTML (from Dynamic Document Templates) to PDF. When you are ready to set up wkhtmltopdf, **check first if it is already installed** (Section 3.0); if so, you can skip or only run verification. Then follow the batches in order and use the verification steps as a checklist.

**Knowledge:** For background on HTML-to-PDF in document generation, wkhtmltopdf and pdfkit, constraints (e.g. absolute image URLs, no `--base-url`), and alternatives, see [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md).

**App context:** PLAN-ADD-DOCUMENT-SETS and DESIGN-DOCS specify **pdfkit** (Python) with **wkhtmltopdf** (system binary) for HTML-to-PDF. The app uses this for generating documents from Dynamic templates; see `apps.documents.services.render_dynamic_template_to_pdf` and the Django system check `documents.W001` (wkhtmltopdf availability).

**Usage:** Treat this as a setup guide, not a code plan. Batches are ordered so each step can be verified before moving on. “Tests” are verification steps (CLI, `manage.py check`, optional test conversion) to confirm the tool is available and working. **Do not duplicate steps** that are already part of another plan (e.g. pdfkit is installed when you run `pip install -r requirements.txt` in PLAN-ADD-DOCUMENT-SETS)—see Section 3.0 and the note before Batch 2.

---

## 1. Summary: What is wkhtmltopdf and how the app uses it

- **wkhtmltopdf** is a command-line tool (WebKit-based) that renders HTML and outputs PDF; it must be installed on the **system**. **pdfkit** is the Python wrapper that invokes it. This app uses them in the Document Sets flow: Dynamic templates → HTML → PDF → stored in DocumentInstanceVersion. Without wkhtmltopdf on PATH, dynamic document generation fails; the app raises `DocumentGenerationError` and the Django check `documents.W001` warns.
- **Image URLs** in the HTML must be **absolute**; many wkhtmltopdf builds do not support `--base-url`. The app builds absolute URLs (e.g. `request.build_absolute_uri(image.file.url)` or SITE_URL). See [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) for full detail.

---

## 2. Prerequisites

- **Python environment** for the project (venv or similar) with the project’s `requirements.txt` installed (so pdfkit is present).
- **Platform:** Linux (including WSL2), macOS, or Windows. Install commands differ by OS; Batches 1–2 cover common cases.

---

## 3. Implementation Order and Batches

### 3.0 Check if wkhtmltopdf is already installed (skip setup if so)

Before installing anything, confirm whether the system and environment are already ready:

1. **Check the binary:** In a terminal, run:
   ```bash
   wkhtmltopdf --version
   ```
   If this prints a version (e.g. "wkhtmltopdf 0.12.6") and exits 0, **wkhtmltopdf is already installed**. You can skip **Batch 1**.
2. **Check the app:** From the project root with your Python environment active, run:
   ```bash
   python manage.py check
   ```
   If there is **no** `documents.W001` (or similar) warning about wkhtmltopdf missing, the app considers wkhtmltopdf available. If you also have pdfkit installed (e.g. you've already run `pip install -r requirements.txt` as part of PLAN-ADD-DOCUMENT-SETS or general project setup), you can **skip Batch 2** as well.
3. **Optional:** Run the Batch 3 shell snippet (Section 3, Batch 3) to confirm end-to-end conversion. If it succeeds, setup is complete and you need not run any batches.

**If both the version command and `manage.py check` succeed:** You are done; no need to run Batches 1–2. Only run the batches for steps that are not yet in place (e.g. binary missing → Batch 1; pdfkit or check still failing → Batch 2).

---

Follow the batches below in sequence. After each batch, run the verification steps before proceeding.

---

### Batch 1: Install wkhtmltopdf (system)

**Goal:** Have the `wkhtmltopdf` binary installed and on PATH so pdfkit can invoke it.

**Steps:**

1. **Choose your platform** and install using one of the following:
   - **Linux (Debian/Ubuntu/WSL2):**
     ```bash
     sudo apt update
     sudo apt install wkhtmltopdf
     ```
     This often installs 0.12.6 or a similar version. If your distro’s package is very old or missing, see the [wkhtmltopdf downloads](https://wkhtmltopdf.org/downloads.html) page for alternate builds.
   - **macOS (Homebrew):**
     ```bash
     brew install wkhtmltopdf
     ```
   - **Windows:** Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html) and run it; ensure the install directory is on your system PATH.
2. **Confirm the binary is on PATH:** Open a **new** terminal (so PATH is refreshed) and run `wkhtmltopdf --version`. You should see a version string (e.g. "wkhtmltopdf 0.12.6").

**Verification (Batch 1):**

- Run `wkhtmltopdf --version`. Expected: version printed (e.g. 0.12.6).
- Run `which wkhtmltopdf` (Linux/macOS) or `where wkhtmltopdf` (Windows). Expected: path to the binary.
- Batch 1 is complete when the version command succeeds and the binary is on PATH in the shell you will use for Django.

---

### Batch 2: Install pdfkit (Python) and verify integration

**Goal:** Ensure the Python environment has pdfkit installed and that the app can see wkhtmltopdf.

**Do not duplicate:** If you are following [70-PLAN-MASTER.md](../70-PLAN-MASTER.md) and will implement (or have already implemented) [40-PLAN-ADD-DOCUMENT-SETS.md](../06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md), that plan already includes adding pdfkit to `requirements.txt` and running `pip install -r requirements.txt`. Do **not** install pdfkit twice—consider it covered by the document plan. Only run the install step below if you have **not** yet installed project requirements (e.g. you are setting up wkhtmltopdf before any document plans). When in doubt, run `pip list | grep -i pdfkit`; if pdfkit is listed, skip the pip install and only run the verification steps (manage.py check and optional Python check).

**Steps:**

1. **Install project dependencies** (including pdfkit):
   ```bash
   pip install -r requirements.txt
   ```
   Or with a venv: `path/to/.venv/bin/pip install -r requirements.txt`.
2. **Run the Django system check:**
   ```bash
   python manage.py check
   ```
   If wkhtmltopdf is missing, you will see a warning like `documents.W001` suggesting installation. After Batch 1, this warning should **not** appear (or should be resolved).
3. **Optional — quick Python check:** In the same environment, run:
   ```bash
   python -c "import pdfkit; print(pdfkit.configuration(wkhtmltopdf='wkhtmltopdf'))"
   ```
   This confirms pdfkit can find the binary (no exception).

**Verification (Batch 2):**

- `pip list | grep -i pdfkit` (or equivalent) shows `pdfkit` installed.
- `python manage.py check` runs without the wkhtmltopdf warning (documents.W001).
- Batch 2 is complete when the app’s check passes and pdfkit can resolve wkhtmltopdf.

---

### Batch 3: Optional — end-to-end test conversion

**Goal:** Confirm that a real HTML string can be converted to PDF through the app’s stack (context build not required; this batch only validates wkhtmltopdf + pdfkit).

**Steps:**

1. From the project root, with the same Python environment and Django settings loaded, run a one-off conversion. Example using the Django shell:
   ```bash
   python manage.py shell -c "
   import pdfkit
   html = '<html><body><h1>Test</h1><p>If you see this PDF, wkhtmltopdf works.</p></body></html>'
   pdf = pdfkit.from_string(html, False, options={})
   print('PDF length:', len(pdf))
   assert len(pdf) > 0, 'Expected non-empty PDF'
   print('OK')
   "
   ```
2. Alternatively, trigger **Generate Documents** from the UI for a deal that has a Document Set Template with a Dynamic template (and required data/images). Confirm a PDF is generated and viewable.

**Verification (Batch 3):**

- The shell snippet prints `PDF length: ...` and `OK` with no exception.
- Or: Generate from the UI produces a document and opening it shows a valid PDF.
- Batch 3 is complete when at least one of these succeeds.

---

## 4. Summary Table

| Step | Goal | When to skip |
|------|------|--------------|
| 3.0 | Check if already installed | — (always run first) |
| Batch 1 | Install wkhtmltopdf on system | Skip if `wkhtmltopdf --version` already succeeds |
| Batch 2 | Install pdfkit and verify app sees binary | Skip pip install if requirements already installed (e.g. via PLAN-ADD-DOCUMENT-SETS); run verification only |
| Batch 3 | Optional end-to-end test | Optional |

| Batch | Verification |
|-------|---------------|
| 1 | `wkhtmltopdf --version` and `which`/`where` succeed |
| 2 | `pip list` shows pdfkit; `manage.py check` has no wkhtmltopdf warning |
| 3 | Shell snippet produces non-empty PDF, or UI Generate produces viewable PDF |

---

## 5. Implementation Notes (for reference)

- **Do not pass `--base-url`:** Many wkhtmltopdf builds (e.g. 0.12.6) do not support it and exit with "Unknown long argument --base-url". The app omits it; image URLs in the HTML are absolute.
- **Image URLs:** When generating with a request, the context builder uses `request.build_absolute_uri(image.file.url)` so wkhtmltopdf can load images. When there is no request (e.g. management command), the app uses `settings.SITE_URL` + relative path; if `SITE_URL` is unset, image loading may fail — document that in the plan or config.
- **Django check:** The app registers `documents.W001` so `manage.py check` warns when wkhtmltopdf is missing. Running check after setup is a good smoke test.

---

## 6. References

- [GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-HTML-TO-PDF.md) — HTML-to-PDF in document generation; wkhtmltopdf and pdfkit; constraints and alternatives.
- [wkhtmltopdf](https://wkhtmltopdf.org/) — project and downloads
- [pdfkit (Python)](https://pypi.org/project/pdfkit/) — PyPI package
- [06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md](../06-DOCS/40-PLAN-ADD-DOCUMENT-SETS.md) — Section 6 (implementation), Section 8 (pdfkit/wkhtmltopdf), Section 12 (image URL handling)
- [06-DOCS/DESIGN-DOCS.md](../06-DOCS/DESIGN-DOCS.md) — Dynamic template → HTML → PDF (pdfkit/wkhtmltopdf)
- [06-DOCS/PHASE-PLANS-DOCS.md](../06-DOCS/PHASE-PLANS-DOCS.md) — Document Sets row (HTML-to-PDF)
- `apps.documents.services` — `check_wkhtmltopdf_available`, `_require_wkhtmltopdf`, `render_dynamic_template_to_pdf`
- `apps.documents.checks` — `documents.W001` system check

---

*When you are ready to set up wkhtmltopdf, run the check in Section 3.0 first; if already installed, skip to verification or Batch 3. Otherwise follow Batches 1 and 2 in order (skipping any step already covered by another plan); add Batch 3 if you want an explicit conversion test.*
