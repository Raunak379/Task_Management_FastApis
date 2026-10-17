# Task Management FastAPI — Documentation Index

This `docs/` folder explains every file and folder in this project, the concepts
behind them, and how everything connects and runs together.

## What this project is

A REST API, built with **FastAPI**, for managing `Task` records in a **MySQL**
database, with **JWT-based user authentication** (register/login) gating every
task endpoint, and a **registration confirmation email** sent in the
background via `fastapi-mail`.

## Tech stack

| Tool | Role |
|---|---|
| FastAPI | web framework — defines HTTP routes, handles requests/responses |
| Uvicorn | ASGI server that actually runs FastAPI |
| SQLAlchemy | ORM — maps Python classes to SQL tables, builds/executes queries |
| PyMySQL | the actual MySQL driver SQLAlchemy uses under the hood |
| Pydantic / pydantic-settings | data validation (request bodies) and settings/env loading |
| PyJWT | encodes/decodes the JSON Web Tokens used for login sessions |
| pwdlib (+ argon2-cffi) | hashes and verifies user passwords (Argon2 algorithm) |
| fastapi-mail (+ aiosmtplib) | sends the "registration confirmation" email over SMTP |

Note: `PyJWT`, `pwdlib`, `argon2-cffi`, `fastapi-mail`, and `aiosmtplib` are
installed in `env/` and required to run the app, but are **not yet listed**
in `requirement.txt` — see `05_issues_and_fixes.md`.

⚠️ **Security note:** `src/utils/mail.py` currently hardcodes a real Gmail
address and app password directly in source. See issue #14 in
`05_issues_and_fixes.md` — fix this before committing/pushing.

## Reading order

1. `01_folder_structure.md` — map of every file/folder and its one-line purpose
2. `02_concepts.md` — the underlying concepts (FastAPI, Pydantic, SQLAlchemy, DI, JWT auth, env vars)
3. `03_file_by_file.md` — deep line-by-line explanation of every file
4. `04_how_to_run.md` — setup, running the server, connecting to MySQL, testing endpoints (including login)
5. `05_issues_and_fixes.md` — bugs/typos found in the current code and how to fix them
