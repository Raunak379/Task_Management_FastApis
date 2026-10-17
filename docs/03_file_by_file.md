# File-by-File Explanation

## `main.py` — the entry point

```python
from fastapi import FastAPI
from src.utils.db import Base, engine
from src.task.router import task_routes
from src.user.router import user_routes

Base.metadata.create_all(engine)
app = FastAPI(title = "this is my task management application ")
app.include_router(task_routes)
app.include_router(user_routes)
```

- Imports `Base` and `engine` from the DB setup, and the two routers.
- `Base.metadata.create_all(engine)` — on startup, creates the `task` and
  `user` tables in MySQL if they don't already exist (based on every model
  class that inherits from `Base`).
- `app = FastAPI(title=...)` — creates the actual application object that
  Uvicorn runs. The `title` shows up on the `/docs` Swagger page. Currently
  has a lowercase "this" and a trailing space — cosmetic, see `05`.
- `app.include_router(task_routes)` / `app.include_router(user_routes)` —
  mounts both feature routers so their endpoints become reachable.
- This file has **no routes of its own** — it's purely composition/wiring.

---

## `src/utils/db.py` — database connection setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.utils.settings import settings

Base = declarative_base()
engine = create_engine(url=settings.DB_CONNECTION)
LocalSession = sessionmaker(bind=engine)

def get_db():
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()
```

- `Base` — the shared parent class every model (`Task`, `user`) inherits from.
- `engine` — reads the MySQL connection string from `settings.DB_CONNECTION`
  and knows how to open real connections to MySQL.
- `LocalSession` — a factory; calling `LocalSession()` produces one new DB
  session bound to that engine.
- `get_db()` — a FastAPI dependency (see `02_concepts.md` §3) that hands out
  one session per request and guarantees it's closed afterward.

---

## `src/utils/settings.py` — typed config loader

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_CONNECTION: str
    SECRET_KEY: str
    ALGORITHM: str
    EXP_TIME: int

settings = settings()
```

- Declares four required environment variables: `DB_CONNECTION` (MySQL URL),
  `SECRET_KEY` and `ALGORITHM` (used to sign/verify JWTs), and `EXP_TIME`
  (token lifetime in minutes).
- `env_file=".env"` tells it to read that file automatically.
- `extra="ignore"` means any other keys in `.env` are silently ignored
  instead of raising an error.
- The last line creates the single instance (`settings`) that the rest of
  the app imports — `src/utils/db.py` uses `settings.DB_CONNECTION`;
  `src/user/controller.py` and `src/utils/helpers.py` use `SECRET_KEY`,
  `ALGORITHM`, and `EXP_TIME` for JWT encode/decode.

---

## `src/utils/constant.py` — currently empty

Placeholder for shared constant values (e.g. status strings, limits) that
would otherwise be duplicated/hardcoded across controllers. Nothing imports
from it yet.

## `src/utils/helpers.py` — JWT auth dependency

```python
def is_authenticated(request:Request, db:Session = Depends(get_db)):
    try:
       token = request.headers.get("authorization")
       if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
       token = token.split(" ")[-1]
       data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
       user_name = data.get("username")
       is_user = db.query(user).filter(user.username == user_name).first()
       if not is_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
       return is_user
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
```

- Reads the `Authorization` header (expected shape: `Bearer <token>`), splits
  off everything after the last space to get the raw token.
- `jwt.decode(...)` verifies the signature with `SECRET_KEY`/`ALGORITHM` and,
  because the payload contains an `exp` claim, **PyJWT automatically rejects
  expired tokens** by raising `ExpiredSignatureError` — a subclass of
  `InvalidTokenError`, so it's caught by the same `except` clause.
- Looks the decoded `username` up in the DB; 401s if the header is missing,
  the token is invalid/expired, or the username no longer matches a real user.
- Returns the `user` row on success — this is what gets injected wherever a
  route declares `Depends(is_authenticated)` (used by every route in
  `src/task/router.py`).
- `src/user/controller.py` has a **second, near-identical** copy of this
  exact function (also named `is_authenticated`, used by `GET /user/is_auth`)
  — see `05_issues_and_fixes.md`.

---

## `src/utils/mail.py` — registration confirmation email

```python
conf = ConnectionConfig(
    MAIL_USERNAME = "sherraunaksingh@gmail.com",
    MAIL_PASSWORD = "ftkl ewtt mpsw ncry",
    MAIL_FROM = "sherraunaksingh@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Raunak FastApi",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_email(email: str):
    html = """<p>Hi, Thanks for registraction. our team will connect you soon !</p> """
    message = MessageSchema(subject="Registration confirmation", recipients=[email],
                             body=html, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)
```

- `ConnectionConfig` (from `fastapi_mail`) describes how to reach the SMTP
  server (Gmail here, port `587` + STARTTLS) and which credentials to log in
  with.
- `send_email(email)` builds an HTML email via `MessageSchema` and sends it
  through `FastMail(conf).send_message(...)`.
- Called from `src/user/controller.py::register` as a **background task**
  (§11 in `02_concepts.md`) right after a new user is committed to the DB —
  so every successful `POST /user/register` triggers a real outbound email.

🚨 **Critical issue:** the Gmail address and **app password** above are
hardcoded directly in this file, not read from `.env`/`settings.py` like
every other secret in the project (`SECRET_KEY`, `DB_CONNECTION`). Combined
with `.gitignore` having no real rules (issue #7), this real credential is
one `git add .` away from being pushed to a remote. See
`05_issues_and_fixes.md` issue #14 — move these into `.env` and
`settings.py` immediately, and rotate/revoke this app password since it has
already been exposed in this conversation/file.

---

## `src/task/models.py` — the `task` SQL table

```python
class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
```

Maps to a MySQL table `task` with 4 columns. `id` auto-increments and is the
primary key. `title` is required at the DB level; `description` may be NULL;
`is_completed` defaults to `False` if not supplied.

## `src/task/dtos.py` — request/response shapes for Task

```python
class TaskSchema(BaseModel):
    title : str
    description : str
    is_completed : bool = False

class TaskResponseSchema(BaseModel):
    id : int
    title : str
    description : str
    is_completed : bool
```

- `TaskSchema` is used by **both** `/task/create` and `/task/update_task/{id}`
  as the request body shape. `title`/`description` are required;
  `is_completed` is optional (defaults to `False`). See `05` for why reusing
  this one schema for *update* forces full-body PUTs.
- `TaskResponseSchema` exists but is **not currently wired up** as a
  `response_model` on any route — see `05`.

## `src/task/controller.py` — task business logic

- `create_task(body, db)` — `model_dump()`s the validated DTO into a dict,
  builds a `Task(...)` row, `add()`+`commit()`+`refresh()`s it, returns
  `{"status": ..., "data": new_task}`.
- `get_task(db)` — `db.query(Task).all()` → returns every row.
- `get_one_task(task_id, db)` — fetches one row by primary key via the
  legacy `db.query(Task).get(task_id)`; raises `HTTPException(404, ...)` if
  not found.
- `update_task(body, task_id, db)` — fetches the row (404 if missing),
  `model_dump()`s the body and loops `setattr(one_task, field, value)` for
  every field (so all three `TaskSchema` fields are always overwritten),
  commits, returns the updated row.
- `delete_task(task_id, db)` — fetches the row (404 if missing),
  `db.delete()`+`db.commit()`s it, returns `None` (paired with the route's
  `204 No Content` status).
- Still imports `from sqlalchemy.orm import session` (lowercase) purely as a
  type hint — not the real `Session` class. See `05`.

## `src/task/router.py` — task HTTP endpoints

Every endpoint requires a valid JWT via `Depends(is_authenticated)`
(`src/utils/helpers.py`) — callers must send `Authorization: Bearer <token>`.

| Method | Path | Calls | Auth required |
|---|---|---|---|
| POST | `/task/create` | `controller.create_task` | yes |
| GET | `/task/all_task` | `controller.get_task` | yes |
| GET | `/task/one_task/{task_id}` | `controller.get_one_task` | yes |
| PUT | `/task/update_task/{task_id}` | `controller.update_task` | yes |
| DELETE | `/task/delete_task/{task_id}` | `controller.delete_task` | yes |

(Recall the `/task` prefix comes from `APIRouter(prefix="/task")`.)

---

## `src/user/models.py` — the `user` SQL table

```python
class user(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
```

`username` and `email` are both `unique=True` at the DB level. The
controller now pre-checks both for duplicates before inserting (see below),
so a normal duplicate signup gets a clean `400` rather than crashing — though
this check-then-insert isn't atomic, so a true race (two simultaneous
signups with the same username) could still hit a raw `IntegrityError`; see
`05_issues_and_fixes.md`.

Note the class is named `user` (lowercase) — unusual; Python convention is
`class User`. It works, but it also shadows the built-in-sounding name and
is easy to confuse with an instance variable (every controller does
`is_user = db.query(user)...`).

## `src/user/dtos.py`

```python
class userSchema(BaseModel):
    username : str
    email : str
    password: str

class userResponseSchema(BaseModel):
    username : str
    email : str
    id : int

class LoginSchema(BaseModel):
    username : str
    password : str
```

- `userSchema` — request body for `POST /user/register`. Takes a **plaintext**
  `password`; the controller hashes it before storing (see below) — it is
  never stored or returned as-is.
- `userResponseSchema` — response shape for `/register` and `/is_auth`;
  deliberately excludes `hashed_password`/`password` so hashes never leak
  back to the client.
- `LoginSchema` — request body for `POST /user/login`: `username` + `password`.

## `src/user/controller.py`

```python
password_hash = PasswordHash.recommended()
def get_password_hash(password):
    return password_hash.hash(password)
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)
```

`pwdlib`'s `PasswordHash.recommended()` picks a modern default algorithm
(Argon2, backed by the `argon2-cffi` package) for hashing/verifying passwords.

- **`register(body, db, bg_task)`** (now `async def`) — checks `username` not
  taken (400 if so), checks `email` not taken (400 if so), hashes
  `body.password` via `get_password_hash`, builds a `user(...)` row with the
  hash stored in `hashed_password`, `add()`+`commit()`+`refresh()`s it, then
  queues `send_email` (`src/utils/mail.py`) as a background task via
  `bg_task.add_task(send_email, [new_user.email])` so a confirmation email
  goes out *after* the response is returned (see `02_concepts.md` §11 for the
  `BackgroundTasks` mechanism, and the list-vs-string argument bug noted
  there). Returns the new row (serialized through `userResponseSchema` by the
  router — hash never leaves the server). Has two leftover commented-out
  lines (`#res = await send_email(...)`, `#print(res)`) from an earlier
  non-background version.
- **`login_user(body, db)`** — looks the user up by `username` (401 "wrong
  password" if not found — deliberately the same message as a wrong password,
  so the API doesn't reveal whether a username exists), verifies
  `body.password` against the stored hash (401 if it doesn't match), then
  builds a JWT:
  ```python
  exp_time = datetime.now() + timedelta(minutes=settings.EXP_TIME)
  token = jwt.encode({"username": is_user.username, "exp": exp_time.timestamp()},
                      settings.SECRET_KEY, settings.ALGORITHM)
  return {"token": token}
  ```
  Has a leftover `print(exp_time)` debug line — harmless but worth removing.
- **`is_authenticated(request, db)`** — an exact duplicate of
  `src/utils/helpers.py`'s function of the same name, used only by
  `GET /user/is_auth`. See `05_issues_and_fixes.md`.

## `src/user/router.py`

| Method | Path | Calls | Auth required |
|---|---|---|---|
| POST | `/user/register` | `controller.register` (sends confirmation email in background) | no |
| POST | `/user/login` | `controller.login_user` | no |
| GET | `/user/is_auth` | `controller.is_authenticated` | yes (JWT) |

`register`'s `response_model=userResponseSchema` and `is_auth`'s same
`response_model` are what strip `hashed_password` out of the JSON response —
FastAPI builds the response by reading only the fields `userResponseSchema`
declares, off of whatever object the controller returns.

`register` here is `async def register(body, bg_task: BackgroundTasks, db =
Depends(get_db))` and `await`s `controller.register(...)`, matching the
controller now being `async` (see above and `02_concepts.md` §11).

There is no `update`/`delete`/`get-all`/`get-by-id` endpoint for users yet —
only register, login, and the auth check.

---

## `.env` — environment-specific secrets

```
DB_CONNECTION = "mysql+pymysql://root:<password>@localhost/task_management"
SECRET_KEY = "<random secret string>"
ALGORITHM = "<e.g. HS256>"
EXP_TIME = <minutes, e.g. 30>
```

- `DB_CONNECTION` — the SQLAlchemy connection URL, shaped
  `dialect+driver://username:password@host/database_name`. Any `@` inside the
  password must be URL-encoded as `%40`.
- `SECRET_KEY` — the key used to sign and verify JWTs (`src/user/controller.py`,
  `src/utils/helpers.py`). Keep this secret — anyone with it can forge valid
  login tokens.
- `ALGORITHM` — the JWT signing algorithm (e.g. `HS256`), passed to both
  `jwt.encode` and `jwt.decode`.
- `EXP_TIME` — how many minutes a login token stays valid before `jwt.decode`
  starts rejecting it as expired.

This file is intentionally excluded from git — but see `.gitignore` below,
which currently doesn't actually enforce that.

## `.gitignore`

Currently only has a comment explaining what `.gitignore` is for — no actual
ignore patterns. The project's `git status` still shows `.env`, `env/`, and
`__pycache__/` as untracked rather than ignored, because the file has no
rules in it. See `05_issues_and_fixes.md`.

## `requirement.txt`

```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
pydantic-settings
```

No version pins, and — now that JWT auth, password hashing, and email
sending exist — **missing `PyJWT`, `pwdlib`, `fastapi-mail`, and
`aiosmtplib` entirely**, even though all four are imported by the code and
installed in `env/`. See `05_issues_and_fixes.md`.

## `env/` and `__pycache__/`

- `env/` — the virtual environment folder itself (created by
  `python -m venv env`). Contains a full copy of the Python interpreter plus
  every installed package. Never edit anything inside it by hand; never commit it.
- `__pycache__/` — auto-generated `.pyc` bytecode cache Python creates to
  speed up subsequent imports. Safe to delete anytime; regenerates automatically.
