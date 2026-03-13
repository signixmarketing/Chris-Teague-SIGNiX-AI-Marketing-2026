# Setup: Student (Windows, no WSL)

**You:** Student on **Windows** **without WSL**. You use **PowerShell** or **Command Prompt** and **Cursor**. You may not have used Git, Python, or this repo before. This file is **self-contained**: follow it only and you’ll get from zero to a running app.

All steps use **native Windows** (no WSL). For the venv you’ll use **`.venv\Scripts\activate`** and **`python`** (or **`py -3`** if you use the Python launcher).

---

## Part A: Do these first (you interact)

### A.1 Install Git and Python on Windows (if needed)

- **Git:** [Git for Windows](https://git-scm.com/download/win) — install and use Git Bash, PowerShell, or Command Prompt for the steps below.
- **Python 3:** [Python 3](https://www.python.org/downloads/) — during setup, **check "Add Python to PATH"**. You need Python 3.10+.

Use **PowerShell** or **Command Prompt** (not necessarily Git Bash) for Part A and Part B so activation and paths are consistent.

### A.2 GitHub authentication

You need to clone the repo. Choose **one** of these.

**Option A — SSH**

1. In a terminal: `ssh -T git@github.com`
2. If you see **"Hi &lt;username&gt;! You've successfully authenticated..."** — use the **SSH** clone URL in A.3.
3. If "Permission denied" or passphrase issues: add your SSH key in GitHub (Settings → SSH and GPG keys) or use Option B.

**Option B — Personal Access Token (recommended if you’re new)**

1. In a browser: [GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens). (Or Settings → scroll to bottom → Developer settings.)
2. **Generate new token (classic)**. Note (e.g. "Course clone"), Expiration, scope **repo**. Generate and **copy the token** (GitHub shows it only once).
3. In A.3 use the **HTTPS** clone URL; when Git asks for a password, paste this token (not your GitHub password).

You must be a member of the **AIsummit2026Q2** organization (or have access to the repo).

### A.3 Clone the repo (PowerShell or Command Prompt)

**If you use SSH:**

```bash
git clone git@github.com:AIsummit2026Q2/proj-template-and-lease-SIGNiX-app.git
cd proj-template-and-lease-SIGNiX-app
```

**If you use a Personal Access Token:**

```bash
git clone https://github.com/AIsummit2026Q2/proj-template-and-lease-SIGNiX-app.git
cd proj-template-and-lease-SIGNiX-app
```

When prompted for **password**, paste your **Personal Access Token**. Clone to a Windows folder (e.g. Desktop or Documents).

---

## Part B: Install and run (you or Cursor can do this)

### B.1 Open the project in Cursor

In Cursor: **File → Open Folder** → select the repo folder (the one that contains `manage.py`). Use the **same shell** (PowerShell or Command Prompt) for all Part B commands.

### B.2 Create environment, install, restore, and start the app

**Option 1 — Copy-paste prompt (easiest)**

Copy the prompt below, paste it into Cursor, and send it. Cursor will create the venv, install dependencies, restore the distribution, and start the server. Then open **http://127.0.0.1:8000/** in your browser and log in with **karl** / **karl**.

> I'm on Windows and I don't use WSL. Do the full installation for this project so I have a working app: create a Python virtual environment (use `python -m venv .venv` or `py -3 -m venv .venv`), activate it with `.venv\Scripts\activate`, install dependencies from requirements.txt, run scripts/restore_distribution.py, then start the Django development server with `python manage.py runserver`. Use Windows paths and this activation. If Git or Python aren't available in this environment, tell me to install Git for Windows and Python 3 from python.org with "Add Python to PATH" and then try again. I want to open http://127.0.0.1:8000/ and log in as karl / karl.

**Option 2 — Run commands yourself**

In Cursor’s terminal (PowerShell or Command Prompt), from the project root (folder that contains `manage.py`):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/restore_distribution.py
python manage.py runserver
```

(If you use the Python launcher: `py -3 -m venv .venv` then `.venv\Scripts\activate`.)

Then open **http://127.0.0.1:8000/** and log in with **karl** / **karl**.

**Option 3 — Cursor Run Task**

In Cursor: **Terminal → Run Task** → **"First-time setup (install + restore)"**. Then start the app with F5 or Run and Debug. Ensure the Python interpreter is set to the project’s **.venv** (`.venv\Scripts\python.exe` on Windows).

---

## Optional: Full app features

The app runs after B.2. For **Generate/Regenerate** documents you need **wkhtmltopdf**; for **SIGNiX push** or a public URL you need **ngrok**. Run the "check first" step for each; if already installed/set up, skip.

- **wkhtmltopdf:** See **[../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md)** — Section 3.0 check; if not installed, Batches 1–2 (Windows: download installer from the downloads page linked there).
- **ngrok:** See **[../PROJECT-DOCS/08-NGROK/10-PLAN-NGROK.md](../PROJECT-DOCS/08-NGROK/10-PLAN-NGROK.md)** — Section 6.0 check; if not set up, Batches 1–3. Set `NGROK_DOMAIN` in `.vscode/launch.json` if you use the "Django with ngrok" profile.

---

## Configure in the app (browser)

Once the app is running and you’re logged in:

- **SIGNiX API credentials** — Sidebar → **SIGNiX Configuration** (`/signix/config/`). Enter your SIGNiX credentials and save.
- **Contact email for signing links** — Set the **email** of signer **contacts** to your test Gmail (or other inbox). Edit contacts in the app.

---

## Cursor: Python interpreter and debug

- Set the Python interpreter to the project’s **.venv** (status bar or Command Palette → "Python: Select Interpreter" → `.venv\Scripts\python.exe`). The repo’s `.vscode/settings.json` may point to `.venv/bin/python` (Linux style); on Windows select the venv manually if needed.
- **Django: runserver** — F5 for local use. **Django with ngrok** — use when you need the tunnel (set `NGROK_DOMAIN` in `.vscode/launch.json` first).

---

## How to create a Personal Access Token (GitHub)

1. Log in to [GitHub](https://github.com).
2. Profile picture (top right) → **Settings**.
3. Left sidebar: scroll down → **Developer settings** ([github.com/settings/tokens](https://github.com/settings/tokens)).
4. **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**.
5. Note (e.g. "Course clone"), Expiration, scope **repo**. Generate.
6. **Copy the token immediately** — GitHub shows it only once. When Git asks for a password, paste this token.

---

## Restore only (you already have the repo)

From the project root in PowerShell or Command Prompt, with venv activated:

```powershell
python scripts/restore_distribution.py
python manage.py runserver
```

Log in as **karl** / **karl**.
