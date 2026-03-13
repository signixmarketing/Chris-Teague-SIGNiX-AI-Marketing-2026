# Setup: Student (Mac)

**You:** Student on a **Mac** with **Cursor**. You may not have used Git, Python, or this repo before. This file is **self-contained**: follow it only and you’ll get from zero to a running app.

All steps use **Terminal** (or Cursor’s integrated terminal). You’ll use **`python3`** and **`source .venv/bin/activate`** for the virtual environment.

---

## Part A: Do these first (you interact)

### A.1 Install Git and Python on the Mac (if needed)

- **Git:** Open Terminal and run `xcode-select --install` to install the Xcode Command Line Tools (includes Git). Follow the prompts.
- **Python 3:** Install from [python.org](https://www.python.org/downloads/) or run `brew install python3` if you use Homebrew. You need Python 3.10+.

Use **`python3`** in the steps below (or **`python`** if it’s Python 3: run `python --version` to check).

### A.2 GitHub authentication

You need to clone the repo. Choose **one** of these.

**Option A — SSH**

1. In Terminal: `ssh -T git@github.com`
2. If you see **"Hi &lt;username&gt;! You've successfully authenticated..."** — use the **SSH** clone URL in A.3.
3. If "Permission denied" or passphrase issues: add your SSH key in GitHub (Settings → SSH and GPG keys) or use Option B.

**Option B — Personal Access Token (recommended if you’re new)**

1. In a browser: [GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens). (Or Settings → scroll to bottom → Developer settings.)
2. **Generate new token (classic)**. Note (e.g. "Course clone"), Expiration, scope **repo**. Generate and **copy the token** (GitHub shows it only once).
3. In A.3 use the **HTTPS** clone URL; when Git asks for a password, paste this token (not your GitHub password).

You must be a member of the **AIsummit2026Q2** organization (or have access to the repo).

### A.3 Clone the repo (Terminal)

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

When prompted for **password**, paste your **Personal Access Token**. Clone to a folder on your Mac (e.g. Desktop or home).

---

## Part B: Install and run (you or Cursor can do this)

### B.1 Open the project in Cursor

In Cursor: **File → Open Folder** → select the repo folder (the one that contains `manage.py`). Use Terminal or Cursor’s integrated terminal for the commands below.

### B.2 Create environment, install, restore, and start the app

**Option 1 — Copy-paste prompt (easiest)**

Copy the prompt below, paste it into Cursor, and send it. Cursor will create the venv, install dependencies, restore the distribution, and start the server. Then open **http://127.0.0.1:8000/** in your browser and log in with **karl** / **karl**.

> I'm on a Mac. Do the full installation for this project so I have a working app: create a Python virtual environment with `python3 -m venv .venv`, activate it with `source .venv/bin/activate`, install dependencies from requirements.txt, run scripts/restore_distribution.py, then start the Django development server with `python manage.py runserver`. If Git or Python aren't available in this environment, tell me to run `xcode-select --install` for Git and to install Python 3 from python.org or run `brew install python3`, then try again. I want to open http://127.0.0.1:8000/ and log in as karl / karl. Remind me that once the application is running I should update my user profile (first name, last name, phone, email), SIGNiX API credentials, and Contacts accordingly.

**Option 2 — Run commands yourself**

In Cursor’s terminal (or Terminal), from the project root (folder that contains `manage.py`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_distribution.py
python manage.py runserver
```

(If only `python` is available and it’s Python 3, use `python -m venv .venv` and `python manage.py runserver`.)

Then open **http://127.0.0.1:8000/** and log in with **karl** / **karl**.

**Option 3 — Cursor Run Task**

In Cursor: **Terminal → Run Task** → **"First-time setup (install + restore)"**. Then start the app with F5 or Run and Debug.

---

## Optional: Full app features

The app runs after B.2. For **Generate/Regenerate** documents you need **wkhtmltopdf**; for **SIGNiX push** or a public URL you need **ngrok**. Run the "check first" step for each; if already installed/set up, skip.

- **wkhtmltopdf:** See **[../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md)** — Section 3.0 check; if not installed, Batches 1–2 (Mac: `brew install wkhtmltopdf` or use the downloads page linked there).
- **ngrok:** See **[../PROJECT-DOCS/08-NGROK/10-PLAN-NGROK.md](../PROJECT-DOCS/08-NGROK/10-PLAN-NGROK.md)** — Section 6.0 check; if not set up, Batches 1–3. Set `NGROK_DOMAIN` in `.vscode/launch.json` if you use the "Django with ngrok" profile.

---

## Configure in the app (browser)

Once the app is running and you’re logged in:

- **User profile** — Update your profile with the correct first name, last name, phone number, and email address (e.g. in the app under your account/profile).
- **SIGNiX API credentials** — Sidebar → **SIGNiX Configuration** (`/signix/config/`). Enter your SIGNiX credentials and save.
- **Contact email and phone for signing links** — Set the **email** and **phone** of signer **contacts** to your test Gmail (or other inbox) and phone. Edit contacts in the app.

---

## Cursor: Python interpreter and debug

- Set the Python interpreter to the project’s **.venv** (status bar or Command Palette → "Python: Select Interpreter" → `.venv/bin/python`).
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

From the project root in Terminal, with venv activated:

```bash
python scripts/restore_distribution.py
python manage.py runserver
```

Log in as **karl** / **karl**.
