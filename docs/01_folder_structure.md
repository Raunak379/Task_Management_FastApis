# Folder Structure

```
Task_Management_FastApis/
├── .env                  # secret config (DB + JWT settings) — NOT committed to git
├── .gitignore            # tells git which files/folders to ignore (see 05 — currently has no real rules)
├── requirement.txt       # list of Python packages this project needs (currently incomplete — see 05)
├── main.py               # the entry point — starts the FastAPI app
├── env/                  # Python virtual environment (isolated interpreter + packages)
├── __pycache__/          # auto-generated compiled bytecode cache, ignore it
└── src/                  # all application source code lives here
    ├── task/              # everything related to "Task" feature
    │   ├── _init_.py        # (see note in 05_issues_and_fixes.md — should be __init__.py)
    │   ├── models.py        # SQLAlchemy table definition for Task
    │   ├── dtos.py           # Pydantic schemas: TaskSchema (request), TaskResponseSchema (response, unused so far)
    │   ├── controller.py     # business logic (DB operations) for tasks — create/read/update/delete
    │   └── router.py         # HTTP routes for tasks — every route requires a valid JWT
    ├── user/              # everything related to "User" feature (register/login/auth)
    │   ├── _init_.py
    │   ├── models.py        # SQLAlchemy table definition for user
    │   ├── dtos.py           # Pydantic schemas: userSchema, userResponseSchema, LoginSchema
    │   ├── controller.py     # register, login_user, is_authenticated (password hashing + JWT)
    │   └── router.py         # HTTP routes: /register, /login, /is_auth
    └── utils/             # shared/cross-cutting code, not tied to one feature
        ├── _init_.py
        ├── db.py             # SQLAlchemy engine/session setup — the DB connection itself
        ├── settings.py       # loads .env into a typed Python object (DB + JWT config)
        ├── constant.py       # currently empty — meant for shared constants
        └── helpers.py        # `is_authenticated` — JWT auth dependency shared across routers
```

## Why split code this way (feature-based structure)

Instead of one giant `main.py`, the project groups code **by feature** (`task`,
`user`) and each feature has the same four building blocks:

- **`models.py`** — what the data looks like *in the database* (the table).
- **`dtos.py`** — what the data looks like *over the network* (the request/response
  shape the API accepts). DTO = "Data Transfer Object".
- **`controller.py`** — the actual logic: talk to the database, apply rules.
- **`router.py`** — wires HTTP methods + URL paths to controller functions.

This is a common layered pattern: **Router → Controller → Model**, with a
**DTO** validating everything that crosses the network boundary. It scales
better than one file, because adding a new feature (e.g. "project") just means
adding a new folder with the same four files — nothing existing has to change.

## `src/utils/` — shared infrastructure

Anything that isn't specific to "task" or "user" but is needed by both lives
in `utils/`: the database connection (`db.py`), configuration (`settings.py`),
and the JWT auth dependency (`helpers.py`). Every endpoint in
`src/task/router.py` depends on `is_authenticated` from `helpers.py` to require
a logged-in user; `src/user/router.py`'s `/is_auth` endpoint also uses it
(via `controller.is_authenticated`, a near-duplicate of the same function —
see `05_issues_and_fixes.md`).
