# Setup: Presenter (WSL, demo with ngrok)

**You:** Presenter in class. You use **WSL** and want to clone the project and run it so the class can access it via your **ngrok** URL. You’ve run the project before (e.g. in another folder), so Git, Python, GitHub auth, and ngrok are already set up.

This file is **self-contained**: follow it only and you’ll get from clone to a running app at your ngrok URL.

---

## What you need before starting

- **WSL** (e.g. Ubuntu) and **Cursor** installed.
- **Git** and **Python 3** (with venv) **inside WSL**. If not: in a WSL terminal run  
  `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip`
- **GitHub:** You can clone the repo (SSH or Personal Access Token). You must be a member of **AIsummit2026Q2** (or have access to the repo).
- **ngrok:** You have an account and know your **authtoken** and **domain hostname** (e.g. `something.ngrok-free.dev` from the [ngrok dashboard](https://dashboard.ngrok.com)).

---

## Quick path (recommended)

1. **Clone** (in a WSL terminal):
   ```bash
   git clone git@github.com:AIsummit2026Q2/proj-template-and-lease-SIGNiX-app.git
   cd proj-template-and-lease-SIGNiX-app
   ```
   (Or use the HTTPS URL and paste your Personal Access Token when Git asks for a password.)

2. **Open in Cursor via WSL:** From the same WSL terminal run `cursor .` (or in Cursor: File → Open Folder → WSL path, e.g. `\\wsl$\Ubuntu\home\YourUser\proj-template-and-lease-SIGNiX-app`).

3. **Copy the prompt below.** Replace **`YOUR_NGROK_DOMAIN`** with your actual ngrok hostname (e.g. `something.ngrok-free.dev`), then paste into Cursor and send. Cursor will do the installation, set your domain in `.vscode/launch.json`, and start ngrok and the Django server.

4. **Open** **https://YOUR_NGROK_DOMAIN** in your browser (use your real domain). Log in with **karl** / **karl**.

---

## Copy-paste prompt (Presenter, with ngrok)

Replace `YOUR_NGROK_DOMAIN` with your ngrok hostname (e.g. `my-demo.ngrok-free.dev`), then paste this into Cursor:

> Do the full installation for this project: create a Python virtual environment, install dependencies from requirements.txt, and run scripts/restore_distribution.py. My ngrok domain is **YOUR_NGROK_DOMAIN**. Update `.vscode/launch.json` so the "Ngrok: tunnel to port 8000" configuration has `NGROK_DOMAIN` set to that domain. Then start ngrok (with that domain on port 8000) and the Django development server so I can access the app at https://YOUR_NGROK_DOMAIN. I will log in as karl / karl.

---

## If you prefer to run steps yourself

### 1. Clone the repo (WSL terminal)

**SSH:**
```bash
git clone git@github.com:AIsummit2026Q2/proj-template-and-lease-SIGNiX-app.git
cd proj-template-and-lease-SIGNiX-app
```

**HTTPS (you’ll be prompted for password = Personal Access Token):**
```bash
git clone https://github.com/AIsummit2026Q2/proj-template-and-lease-SIGNiX-app.git
cd proj-template-and-lease-SIGNiX-app
```

### 2. Open the project in Cursor via WSL

From the WSL terminal: `cursor .`  
Or in Cursor: File → Open Folder → your WSL path (e.g. `\\wsl$\Ubuntu\home\YourUser\proj-template-and-lease-SIGNiX-app`).  
This keeps the integrated terminal and Python environment in WSL.

### 3. Create environment, restore, and run with ngrok

In Cursor’s terminal (WSL), or in a WSL terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/restore_distribution.py
```

Set your ngrok domain in `.vscode/launch.json`: in the "Ngrok: tunnel to port 8000" configuration, set `NGROK_DOMAIN` to your hostname (e.g. `my-demo.ngrok-free.dev`).

Start the app with ngrok: use the **"Django with ngrok"** launch profile (Run and Debug → "Django with ngrok") so both the tunnel and Django start. Or run in two terminals: `ngrok http --domain=YOUR_DOMAIN 8000` and `python manage.py runserver`.

Open **https://YOUR_NGROK_DOMAIN** in your browser. Log in with **karl** / **karl**.

---

## Optional: Configure in the app

Once the app is running:

- **SIGNiX API credentials** — Sidebar → **SIGNiX Configuration** (`/signix/config/`). Enter your SIGNiX credentials and save.
- **Contact email for signing links** — Set signer **contacts**’ email to your test Gmail (or other inbox) so you receive signing links.

---

## Optional: wkhtmltopdf

For **Generate/Regenerate** documents you need wkhtmltopdf. See **[../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md](../PROJECT-DOCS/05-SETUP-WKHTMLTOPDF/SETUP-WKHTMLTOPDF.md)** (Section 3.0 check first; if not installed, Batches 1–2).

---

## Cursor: Python interpreter and launch

- Set the Python interpreter to the project’s **.venv** (status bar or Command Palette → "Python: Select Interpreter").
- **Django: runserver** — local only (F5).
- **Django with ngrok** — use for the demo; set `NGROK_DOMAIN` in `.vscode/launch.json` first.

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

From the project root in WSL, with venv activated:

```bash
python scripts/restore_distribution.py
python manage.py runserver
```

Log in as **karl** / **karl**.
