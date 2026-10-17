# How To Run & Connect Everything

## 1. Prerequisites

- Python 3.9+ installed
- MySQL server running locally (since `.env` points at `localhost`)
- A MySQL database named `task_management` already created:
  ```sql
  CREATE DATABASE task_management;
  ```
  (`Base.metadata.create_all(engine)` creates **tables** inside a database,
  it does not create the database itself.)

## 2. Create & activate the virtual environment

The `env/` folder already exists in this project. To activate it:

```bash
# macOS / Linux
source env/bin/activate
```

If it didn't exist, you'd create it with:
```bash
python3 -m venv env
source env/bin/activate
```

You'll know it's active because your shell prompt shows `(env)` at the start.

## 3. Install dependencies

```bash
pip install -r requirement.txt
```

⚠️ **`requirement.txt` is currently incomplete.** The code imports `jwt`
(PyJWT) and `pwdlib` for authentication, and `fastapi_mail` for the
registration confirmation email, but none of these are listed in the file.
Until that's fixed (see `05_issues_and_fixes.md`), also run:

```bash
pip install PyJWT "pwdlib[argon2]" fastapi-mail
```

(All are already present in this repo's `env/` folder if you're reusing it
instead of creating a fresh one.)

## 4. Configure `.env`

Already present at the project root, with four required keys:
```
DB_CONNECTION = "mysql+pymysql://root:<password>@localhost/task_management"
SECRET_KEY = "<any random string>"
ALGORITHM = "HS256"
EXP_TIME = 30
```
- Update `DB_CONNECTION`'s username/password/host/database name to match your
  own MySQL setup.
- `SECRET_KEY` signs login tokens — use a long random value, never commit a
  real one to a public repo.
- `ALGORITHM` must be a JWT algorithm PyJWT supports (`HS256` is the common
  default for a single shared secret).
- `EXP_TIME` is the login token lifetime in minutes.

`src/utils/settings.py` reads all four automatically on startup — no code
changes needed. If any is missing, startup fails fast with a clear
validation error instead of a confusing runtime crash later.

⚠️ **Email credentials are not in `.env` at all.** `src/utils/mail.py`
hardcodes a real Gmail address + app password directly in source instead of
reading them from settings. See issue #14 in `05_issues_and_fixes.md` — until
that's fixed, every successful registration below will attempt to send a
**real email** through that hardcoded account.

## 5. Run the server

```bash
uvicorn main:app --reload
```

- `main` — the file `main.py`.
- `app` — the `FastAPI()` instance defined inside it.
- `--reload` — restarts the server automatically whenever you edit a file
  (great for development, remove it in production).

You should see log lines like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## 6. Explore & test the API

FastAPI auto-generates interactive docs — open in a browser:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Swagger's "Authorize" button lets you paste a bearer token once and have it
auto-attached to every protected request — useful once you have a token from
step 2 below.

### Example requests with `curl`

**Every `/task/*` endpoint requires a JWT.** Register and log in first.

**1. Register a user:**
```bash
curl -X POST http://127.0.0.1:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "angad", "email": "angad14723@gmail.com", "password": "a-real-password"}'
```
Returns `{"username": ..., "email": ..., "id": ...}` — no password/hash in the response.
This also queues a confirmation email in the background (§4 above) — the
response doesn't wait on it, but it will attempt to send over SMTP right
after.

**2. Log in to get a token:**
```bash
curl -X POST http://127.0.0.1:8000/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "angad", "password": "a-real-password"}'
```
Returns `{"token": "<jwt>"}`. Save that token — it expires after `EXP_TIME` minutes.

**3. Check the token works:**
```bash
curl http://127.0.0.1:8000/user/is_auth \
  -H "Authorization: Bearer <jwt>"
```

**4. Create a task (now using the token):**
```bash
curl -X POST http://127.0.0.1:8000/task/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt>" \
  -d '{"title": "Buy milk", "description": "2% milk", "is_completed": false}'
```

**5. Get all tasks:**
```bash
curl http://127.0.0.1:8000/task/all_task \
  -H "Authorization: Bearer <jwt>"
```

**6. Get one task:**
```bash
curl http://127.0.0.1:8000/task/one_task/1 \
  -H "Authorization: Bearer <jwt>"
```

**7. Update a task** (remember: **all three fields are currently required** —
see `05_issues_and_fixes.md`):
```bash
curl -X PUT http://127.0.0.1:8000/task/update_task/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt>" \
  -d '{"title": "Buy milk", "description": "whole milk this time", "is_completed": true}'
```

**8. Delete a task:**
```bash
curl -X DELETE http://127.0.0.1:8000/task/delete_task/1 \
  -H "Authorization: Bearer <jwt>"
```
Returns `204 No Content` on success.

Omitting the `Authorization` header (or sending an expired/invalid token) on
any `/task/*` call or `/user/is_auth` returns `401 Unauthorized`.

## 7. How the pieces connect, end to end

```
MySQL  <-- pymysql driver <-- SQLAlchemy engine (src/utils/db.py)
                                      |
                              LocalSession (per-request DB session)
                                      |
                        get_db() dependency (Depends)
                                      |
                is_authenticated dependency (src/utils/helpers.py)
                    (decodes JWT, loads the user row — task routes only)
                                      |
                       controller.py  <->  models.py (Task / user classes)
                                      |
                          router.py (APIRouter, HTTP paths)
                                      |
                     main.py (include_router, FastAPI() app)
                                      |
                              Uvicorn (ASGI server)
                                      |
                              your HTTP client (curl / browser / Postman)
```

`settings.py` feeds the DB connection string and JWT config (from `.env`)
into `db.py` and `helpers.py`/`user/controller.py` at import time — that's
the one place config, the database layer, and the auth layer all connect.
