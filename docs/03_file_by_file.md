# File-by-File Explanation

## `main.py` — the entry point

```python
from fastapi import FastAPI
from src.utils.db import Base, engine
from src.task.router import task_routes
from src.user.router import user_routes

Base.metadata.create_all(engine)
app = FastAPI(title="this is my task management application ")
app.include_router(task_routes)
app.include_router(user_routes)
```

- Imports `Base` and `engine` from the DB setup, and the two routers.
- `Base.metadata.create_all(engine)` — on startup, creates the `task` and
  `user` tables in MySQL if they don't already exist (based on every model
  class that inherits from `Base`).
- `app = FastAPI(title=...)` — creates the actual application object that
  Uvicorn runs. The `title` shows up on the `/docs` Swagger page.
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

settings = settings()
```

- Declares that the app needs exactly one environment variable,
  `DB_CONNECTION`, and that it must be a string.
- `env_file=".env"` tells it to read that file automatically.
- `extra="ignore"` means any other keys in `.env` are silently ignored
  instead of raising an error.
- The last line creates the single instance (`settings`) that the rest of
  the app imports — e.g. `src/utils/db.py` uses `settings.DB_CONNECTION`.

---

## `src/utils/constant.py` and `src/utils/helpers.py`

Both are currently **empty**. They exist as placeholders for:
- `constant.py` — shared constant values (e.g. status strings, limits) that
  would otherwise be duplicated/hardcoded across controllers.
- `helpers.py` — small reusable utility functions (e.g. password hashing,
  date formatting) shared by multiple features.

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

## `src/task/dtos.py` — request validation shape for Task

```python
class TaskSchema(BaseModel):
    title: str
    description: str
    is_completed: bool = False
```

Used by **both** `/task/create` and `/task/update_task/{id}`. `title` and
`description` are required in the request body; `is_completed` is optional
(defaults to `False`). See `05_issues_and_fixes.md` for why reusing this one
schema for *update* is a problem.

## `src/task/controller.py` — task business logic

- `create_task(body, db)` — `model_dump()`s the validated DTO into a dict,
  builds a `Task(...)` row, `add()`+`commit()`+`refresh()`s it, returns it.
- `get_task(db)` — `db.query(Task).all()` → returns every row.
- `get_one_task(task_id, db)` — fetches one row by primary key; raises
  `HTTPException(404, ...)` if not found.
- `update_task(body, task_id, db)` — fetches the row (404 if missing),
  overwrites all three fields from `body`, commits, returns the updated row.
- There is **no delete function**, despite the file's top comment mentioning
  "read, delete, update, create."

## `src/task/router.py` — task HTTP endpoints

| Method | Path | Calls |
|---|---|---|
| POST | `/task/create` | `controller.create_task` |
| GET | `/task/all_task` | `controller.get_task` |
| GET | `/task/one_task/{task_id}` | `controller.get_one_task` |
| PUT | `/task/update_task/{task_id}` | `controller.update_task` |

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

`username` and `email` are both `unique=True` — MySQL will reject a second
row with a duplicate value (raises an SQLAlchemy `IntegrityError`, which is
currently **not caught** anywhere — see `05_issues_and_fixes.md`).

Note the class is named `user` (lowercase) — unusual; Python convention is
`class User`. It works, but it also shadows the built-in-sounding name and
is easy to confuse with an instance variable.

## `src/user/dtos.py`

```python
class userSchema(BaseModel):
    username: str
    email: str
    hashed_password: str
```

Despite the name `hashed_password`, nothing in this codebase actually hashes
anything yet — the client is expected to send an already-hashed value, or
(more likely, if this is still early-stage) a plaintext password is stored
directly under a misleading name. See `05_issues_and_fixes.md`.

## `src/user/controller.py`

- `create_user(body, db)` — same pattern as `create_task`: dict → model →
  add/commit/refresh → return.
- `get_user(db)` — returns all users. Note: this returns `hashed_password`
  directly in the JSON response — a real security issue (see `05`).

## `src/user/router.py`

| Method | Path | Calls |
|---|---|---|
| POST | `/user/create` | `controller.create_user` |
| GET | `/user/all_user` | `controller.get_user` |

No `one_user/{id}`, `update`, or `delete` endpoints exist yet for users.

---

## `.env` — environment-specific secrets

```
DB_CONNECTION = "mysql+pymysql://root:<password>/localhost/task_management"
```

This is the SQLAlchemy connection URL, shaped:
`dialect+driver://username:password@host/database_name`

- `mysql` — the database type.
- `pymysql` — the Python driver SQLAlchemy should use to actually talk to MySQL.
- `root` — the MySQL username.
- the password — note any `@` character inside a password must be
  URL-encoded as `%40` (this file does that correctly).
- `localhost` — the DB server is running on the same machine.
- `task_management` — the database name to connect to (must already exist
  in MySQL — `create_all` creates *tables*, not the database itself).

This file is intentionally excluded from git via `.gitignore` so credentials
never get pushed to GitHub.

## `.gitignore`

Currently only has a comment explaining what `.gitignore` is for, but the
project's actual `git status` shows `.env`, `env/`, and `__pycache__/` are
still **untracked** rather than ignored — meaning the file's ignore *rules*
are missing. See `05_issues_and_fixes.md`.

## `requirement.txt`

```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
pydantic-settings
```

No version pins (e.g. `fastapi==0.115.0`) — see `05_issues_and_fixes.md` for
why that can bite you later.

## `env/` and `__pycache__/`

- `env/` — the virtual environment folder itself (created by
  `python -m venv env`). Contains a full copy of the Python interpreter plus
  every installed package. Never edit anything inside it by hand; never commit it.
- `__pycache__/` — auto-generated `.pyc` bytecode cache Python creates to
  speed up subsequent imports. Safe to delete anytime; regenerates automatically.
