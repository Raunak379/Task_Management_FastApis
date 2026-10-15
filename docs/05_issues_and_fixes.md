# Issues Found & Suggested Fixes

Real problems spotted while reading the current code — not hypothetical.
None have been fixed in the source yet; this is a reference for when you
want to clean them up. Items marked **RESOLVED** describe something an
earlier version of this project had, which the current code has already fixed.

## 1. `_init_.py` instead of `__init__.py` (single underscore vs double)

`src/task/_init_.py`, `src/user/_init_.py`, `src/utils/_init_.py` all use a
**single** underscore. Python package init files need **double**
underscores on both sides: `__init__.py`. As written, these files do nothing
— Python 3 still treats the folders as "namespace packages" without them
(so imports happen to keep working), but any code you put inside these files
expecting it to run on import (e.g. re-exports) would silently never execute.

**Fix:** rename to `__init__.py` if you intend to use them for anything, or
delete them if they're meant to stay empty placeholders.

## 2. `update_task` reuses the full `TaskSchema`, forcing full-body PUTs

`src/task/dtos.py` — `TaskSchema` requires `title` and `description`.
Sending a partial update like `{"is_completed": true}` to
`PUT /task/update_task/{id}` still returns `422 Unprocessable Entity`.

**Fix:** add a dedicated, fully-optional update schema:
```python
class UpdateTaskSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None
```
and in the controller, only overwrite fields that were actually sent:
```python
for field, value in body.model_dump(exclude_unset=True).items():
    setattr(one_task, field, value)
```

## 3. User passwords stored/returned in plaintext — **RESOLVED**

The current `src/user/controller.py` hashes `body.password` with `pwdlib`'s
`PasswordHash.recommended()` (Argon2) before storing it, and
`userResponseSchema` (used as every user route's `response_model`) excludes
the hash from responses entirely. No further action needed here.

## 4. No duplicate-signup handling — mostly resolved, one edge case left

`register()` now pre-checks `username` and `email` for uniqueness and raises
a clean `400` before attempting the insert — a big improvement over letting
a raw `IntegrityError` crash with a `500`.

This is still a **check-then-insert** race: two requests that both pass the
uniqueness check before either commits can both reach `db.add()`, and the
second `commit()` would raise an uncaught `IntegrityError` → raw `500`.
Low-probability in practice, but worth hardening if this ever sees real
concurrent traffic.

**Fix:** wrap the final `db.commit()` in a try/except and translate
`IntegrityError` into an `HTTPException(400, ...)` as a backstop, in addition
to the existing pre-checks.

## 5. `db.query(Task).get(task_id)` is deprecated (legacy SQLAlchemy 1.x API)

Used in `task/controller.py` (`get_one_task`, `update_task`, `delete_task`).
SQLAlchemy 2.0 deprecates `Query.get()`; the modern equivalent is:
```python
db.get(Task, task_id)
```

## 6. `from sqlalchemy.orm import session` (lowercase) is not the real `Session` type

`src/task/controller.py` still imports `session` (lowercase) and uses it
only as a type hint (`db: session`). The actual SQLAlchemy session class is
`Session` (capital S); the lowercase `session` is a different internal
module, not a type, so this hint provides no real type-checking benefit even
though it happens not to crash at runtime.

Note: `src/user/controller.py` and `src/user/router.py` already do this
correctly (`from sqlalchemy.orm import Session`) — only the task side still
has the stale import.

**Fix:**
```python
from sqlalchemy.orm import Session
def create_task(body: TaskSchema, db: Session):
```

## 7. `.gitignore` has no actual ignore rules

The file only contains a comment. As a result `.env`, `env/`, and
`__pycache__/` all show up as **untracked** in `git status` instead of being
silently ignored — meaning someone could accidentally `git add .` and commit
real DB credentials *and* your JWT `SECRET_KEY`.

**Fix — add these lines to `.gitignore`:**
```
.env
env/
__pycache__/
*.pyc
```

## 8. `requirement.txt` is missing real dependencies and has no version pins

```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
pydantic-settings
```
Two packages the code actually imports — **`PyJWT`** (`import jwt`) and
**`pwdlib`** (password hashing) — aren't listed at all. A fresh
`pip install -r requirement.txt` on a clean machine would fail at runtime
with `ModuleNotFoundError` the moment `/user/register` or `/user/login` is
hit. None of the five listed packages have version pins either, so a future
install could pull breaking major-version updates without warning.

**Fix:**
```
fastapi
uvicorn[standard]
sqlalchemy
pymysql
pydantic-settings
PyJWT
pwdlib[argon2]
```
Then once the environment is in a known-good state, pin exact versions with
`pip freeze > requirement.txt` (or at minimum pin major versions, e.g.
`fastapi>=0.140,<0.150`). Also consider renaming the file to the conventional
`requirements.txt` (plural) — most tooling/tutorials assume that name.

## 9. No `DELETE`/update/get-by-id endpoints for users

`task` now has full CRUD (`create`, `all_task`, `one_task/{id}`,
`update_task/{id}`, `delete_task/{id}`), but `user` only has `register`,
`login`, and `is_auth` — there's no way to list users, fetch one by id,
update a profile, change a password, or delete an account.

## 10. `FastAPI(title="this is my task management application ")`

`main.py` — lowercase "this" and a trailing space. Purely cosmetic (shows on
the `/docs` page title), but easy to fix:
```python
app = FastAPI(title="This is my task management application")
```

## 11. Duplicate `is_authenticated` function

`src/utils/helpers.py::is_authenticated` and
`src/user/controller.py::is_authenticated` are near-identical copies of the
same function (same header parsing, same JWT decode, same DB lookup) —
`src/task/router.py` depends on the `helpers.py` version, while
`src/user/router.py`'s `/is_auth` endpoint depends on the `controller.py`
version. Any future fix (e.g. re-enabling the commented-out expiry check,
changing the error message) has to be made in two places or they'll drift.

**Fix:** delete the copy in `src/user/controller.py` and have
`src/user/router.py` import `is_authenticated` from `src/utils/helpers.py`
instead, the same way `src/task/router.py` already does.

## 12. Dead/commented-out code and a leftover debug `print`

- `src/user/controller.py::login_user` has `print(exp_time)` — a debug
  leftover that will spam stdout on every login in production.
- Both copies of `is_authenticated` carry a commented-out manual expiry
  check (`#if current_time > exp_time: ...`). It's redundant — PyJWT already
  rejects expired tokens automatically because the payload includes an `exp`
  claim — but the dead code should either be removed or left with a one-line
  comment explaining *why* it's unnecessary, so a future reader doesn't
  "fix" an expiry bug that doesn't exist.

## 13. `TaskResponseSchema` is defined but unused

`src/task/dtos.py` declares `TaskResponseSchema`, but no route in
`src/task/router.py` sets it as a `response_model`. Every task route still
returns the raw SQLAlchemy object (or a dict wrapping it), so the OpenAPI
schema for task responses doesn't reflect reality, and FastAPI can't
auto-strip any field you later add to the model but don't want exposed.

**Fix:** add `response_model=TaskResponseSchema` (or a list/dict-wrapped
variant) to the task routes, the same way `src/user/router.py` already does
with `userResponseSchema`.
