# Core Concepts

## 1. FastAPI — the web framework

FastAPI turns Python functions into HTTP endpoints using decorators:
Decorators:- A decorator is a function that adds extra functionality to another function without changing its original code.

```python
@task_routes.get("/all_task")
def get_all_task(db = Depends(get_db)):
    ...
```

- The decorator (`@task_routes.get(...)`) says: "when an HTTP GET request hits
  this URL, call this function."
- FastAPI reads the function's **type hints** (e.g. `task_id: int`,
  `body: TaskSchema`) and automatically:
  - parses the incoming request (URL path, query params, JSON body)
  - validates it against those types
  - returns `422 Unprocessable Entity` automatically if validation fails
  - generates interactive API docs (Swagger UI at `/docs`, ReDoc at `/redoc`)

## 2. `APIRouter` — grouping related endpoints

```python
task_routes = APIRouter(prefix="/task")

@task_routes.post("/create")   # becomes POST /task/create
```

An `APIRouter` is a mini sub-application. You define routes on it, then
"mount" it onto the main `FastAPI()` app with `app.include_router(...)`
(done in `main.py`). The `prefix` is prepended to every route inside it, so
you don't repeat `/task` on every single endpoint.

## 3. Dependency Injection — `Depends(get_db)`:- Instead of a function creating everything it needs by itself, we provide (inject) those required things from outside.,,Chef → Market → Buy ingredients → Cook,,,,,Supplier → Ingredients → Chef → Cook

```python
def create_task(body: TaskSchema, db = Depends(get_db)):
```

`Depends(get_db)` tells FastAPI: "before running this function, call `get_db()`
and pass its result in as `db`." This is how every route gets a fresh database
session without manually opening/closing one in every function.

session:- Think of session as a connection/working interface that allows your Python code to communicate with the database.

`get_db` (in `src/utils/db.py`) is a **generator function** using `yield`:

```python
def get_db():
    session = LocalSession()
    try:
        yield session       # <- this is what gets injected as `db`
    finally:
        session.close()     # <- runs automatically after the request finishes
```

FastAPI calls this, grabs the value at `yield`, runs your route, and once the
response is sent, resumes the generator so the `finally: session.close()` runs.
This guarantees the DB connection is always closed, even if the route raises
an exception.

## 4. Pydantic — validation via DTOs

```python
class TaskSchema(BaseModel):
    title: str
    description: str
    is_completed: bool = False
```

When a route declares `body: TaskSchema`, FastAPI expects a JSON body shaped
like `{"title": "...", "description": "...", "is_completed": false}`.

- Fields **without** a default (`title`, `description`) are **required**.
- Fields **with** a default (`is_completed: bool = False`) are **optional**.
- If the client omits a required field or sends the wrong type, FastAPI
  returns a `422` error automatically, before your controller code even runs.
- `body.model_dump()` converts the validated Pydantic object back into a
  plain Python `dict`, which is what the controller uses to build the
  SQLAlchemy model instance.

## 5. SQLAlchemy — the ORM (Object-Relational Mapper)

ORM = you write Python classes, SQLAlchemy turns them into SQL tables/queries.

```python
class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
```

- `Base` (from `declarative_base()`) is the parent class every model inherits
  from — it's what lets SQLAlchemy know "this class maps to a table."
- `Column(...)` defines one column: its SQL type (`Integer`, `String(255)`,
  `Boolean`), and constraints (`nullable=False`, `unique=True`, `primary_key=True`).
- `Base.metadata.create_all(engine)` (in `main.py`) looks at every model class
  that inherits from `Base` and issues `CREATE TABLE IF NOT EXISTS` for each.

### Engine, Session, and queries

```python
engine = create_engine(url=settings.DB_CONNECTION)   # knows HOW to talk to MySQL
LocalSession = sessionmaker(bind=engine)              # a factory that produces sessions
```

- **Engine**: manages the actual connection pool to MySQL.
- **Session**: a single "conversation" with the database — tracks objects you
  add/query within one request, and commits/rolls back as a unit.
- Typical flow seen in every controller:
  ```python
  db.add(new_task)     # stage an INSERT
  db.commit()           # actually write it to MySQL
  db.refresh(new_task)  # re-read the row (to get the auto-generated `id`, etc.)
  ```
  ```python
  db.query(Task).all()         # SELECT * FROM task
  db.query(Task).get(task_id)  # SELECT * FROM task WHERE id = task_id (legacy style, see 05)
  ```

## 6. Settings & environment variables (`.env`)

Secrets and environment-specific config (DB URL, API keys, etc.) are kept out
of the source code and put in a `.env` file instead — this file is listed in
`.gitignore` so it's never pushed to GitHub.

```python
class settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DB_CONNECTION: str

settings = settings()
```

`pydantic-settings`'s `BaseSettings` automatically reads `.env`, matches keys
to the class's typed fields (`DB_CONNECTION`), and validates them — so if
`.env` is missing the variable, you get a clear startup error instead of a
confusing runtime crash later.

## 7. JWT authentication — register, login, protect

Three settings in `.env` drive this: `SECRET_KEY`, `ALGORITHM`, `EXP_TIME`.

**Register** (`POST /user/register`): `src/user/controller.py::register` checks
`username`/`email` aren't already taken, hashes the plaintext `password` with
`pwdlib`'s `PasswordHash.recommended()`, and stores the hash as
`hashed_password`. The response uses `userResponseSchema` so the hash is never
returned to the client.

**Login** (`POST /user/login`): `login_user` looks the user up by username,
verifies the password against the stored hash, then builds a JWT:

```python
token = jwt.encode(
    {"username": is_user.username, "exp": exp_time.timestamp()},
    settings.SECRET_KEY,
    settings.ALGORITHM,
)
```

`exp` is the token's expiry (`now + EXP_TIME minutes`). The client is expected
to store this token and send it back on every subsequent request.

**Protecting routes** (`Depends(is_authenticated)`): every task endpoint in
`src/task/router.py`, plus `GET /user/is_auth`, depends on
`is_authenticated` (`src/utils/helpers.py`):

```python
def is_authenticated(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("authorization")   # "Bearer <token>"
    token = token.split(" ")[-1]
    data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
    user_name = data.get("username")
    is_user = db.query(user).filter(user.username == user_name).first()
    ...
    return is_user   # injected into the route as `is_user`
```

So the client must send `Authorization: Bearer <token>` on every protected
call. If the header is missing, the token is malformed/invalid, or the
decoded username no longer matches a real user, this raises `401
Unauthorized` before the route body ever runs — the same DI pattern as
`Depends(get_db)` (§3), just returning a `user` row instead of a session.

Note: `src/user/controller.py` has a **second, near-identical** copy of this
same function (also called `is_authenticated`) that nothing currently calls —
see `05_issues_and_fixes.md`.

## 8. The `DELETE` endpoint

```python
@task_routes.delete("/delete_task/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id:int, db = Depends(get_db), is_user:user = Depends(is_authenticated)):
    return controller.delete_task(task_id, db)
```

`controller.delete_task` fetches the row by id (404 if missing), `db.delete(one_task)`,
`db.commit()`s, and returns `None`. `204 No Content` means a successful response has
no body — FastAPI enforces this, so returning `None` is correct here (returning a
dict with a `204` status would actually raise an error).

Note: `src/task/dtos.py` also defines a `TaskResponseSchema`, but no route currently
declares it as a `response_model` — every task route still returns the raw
SQLAlchemy `Task` object (or a dict wrapping it) and lets FastAPI's default
encoder serialize it.

## 9. Virtual environment (`env/`) and `requirement.txt`

- `env/` is an isolated Python installation just for this project, created
  with `python -m venv env`. It keeps this project's package versions
  separate from other projects / your system Python.
- `requirement.txt` lists the packages the project depends on
  (fastapi, uvicorn, sqlalchemy, pymysql, pydantic-settings). Installed with:
  ```
  pip install -r requirement.txt
  ```
  (Note: the conventional filename is `requirements.txt`, plural — see 05.)

## 10. How a single request flows end-to-end

Example: `POST /task/create` with body `{"title": "Buy milk", "description": "2%"}`
and header `Authorization: Bearer <token-from-login>`.

1. Uvicorn receives the raw HTTP request, hands it to the FastAPI `app`.
2. FastAPI matches the path `/task/create` + method `POST` to
   `create_task()` in `src/task/router.py`.
3. FastAPI resolves `Depends(get_db)` → opens a new DB session.
4. FastAPI resolves `Depends(is_authenticated)` (§7) → reads the `Authorization`
   header, decodes the JWT, looks up the matching user row. If this fails,
   a `401` is returned here and steps 5+ never run.
5. FastAPI validates the JSON body against `TaskSchema` → builds a `body` object.
6. `router.py` calls `controller.create_task(body, db)`.
7. The controller converts `body` to a dict, builds a `Task(...)` SQLAlchemy
   instance, `db.add()`s and `db.commit()`s it — this issues the actual
   `INSERT INTO task (...)` SQL to MySQL.
8. The controller returns a dict `{"status": ..., "data": new_task}`.
9. FastAPI serializes that return value to JSON and sends the HTTP response.
10. After the response is sent, the `get_db` generator resumes and closes the session.
