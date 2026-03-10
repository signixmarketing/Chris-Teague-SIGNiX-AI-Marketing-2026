# Distribution bundle for class

This folder contains a snapshot of the application state so students can load it after cloning the repo.

- **db.sqlite3** — Database (users, deals, templates, document sets, etc.).
- **media.tar.gz** — Archive of uploaded/generated files (templates, documents, images).

## Restore (students)

From the project root, after installing dependencies and (optionally) running migrations:

```bash
python scripts/restore_distribution.py
```

Then start the app:

```bash
python manage.py runserver
```

See the project README or docs for login details.
