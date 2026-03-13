# Distribution bundle for class

This folder contains a snapshot of the application state so you can load it after cloning the repo:

- **db.sqlite3** — Database (users, deals, templates, document sets, etc.).
- **media.tar.gz** — Archive of uploaded/generated files (templates, documents, images).

To get from **clone to a running app**, use **one** of the setup guides below. Each guide is **self-contained** and includes everything you need for that profile (prerequisites, clone, install, restore, run, and a copy-paste prompt for Cursor).

---

## Choose your profile

Pick the guide that matches you:

| Profile | Guide | When to use it |
|--------|--------|-----------------|
| **Presenter (WSL, demo with ngrok)** | [SETUP-PRESENTER-WSL.md](SETUP-PRESENTER-WSL.md) | You’re presenting in class, use WSL, and want the app reachable via your ngrok URL. You’ve run the project before; Git, Python, and ngrok are already set up. |
| **Student — Windows with WSL** | [SETUP-STUDENT-WINDOWS-WSL.md](SETUP-STUDENT-WINDOWS-WSL.md) | You’re on Windows, have WSL (e.g. Ubuntu) and Cursor. You may be new to Git/Python. All terminal steps run inside WSL. |
| **Student — Windows (no WSL)** | [SETUP-STUDENT-WINDOWS-NATIVE.md](SETUP-STUDENT-WINDOWS-NATIVE.md) | You’re on Windows without WSL. You use PowerShell or Command Prompt and Cursor. You may be new to Git/Python. |
| **Student — Mac** | [SETUP-STUDENT-MAC.md](SETUP-STUDENT-MAC.md) | You’re on a Mac with Cursor. You use Terminal. You may be new to Git/Python. |

Open the guide for your profile and follow it from start to finish. Each guide includes a **copy-paste prompt** you can use in Cursor to do the installation and run the app.

---

## After you’re running

- Log in with **karl** / **karl** (or the credentials noted in your guide).
- For **SIGNiX** and **contact emails**, see the “Configure in the app” section in your guide.
- For **document generation** (Generate/Regenerate) you may need wkhtmltopdf; for **SIGNiX push** or a public URL you may need ngrok. Your guide links to the project docs for those.
