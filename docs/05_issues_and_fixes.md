# Issues Found & Suggested Fixes

These are real problems spotted while reading the current code — not
hypothetical. None have been fixed in the source yet; this is a reference
for when you want to clean them up.

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

`src/task/router.py:25` and `dtos.py` — `TaskSchema` requires `title` and
`description`. Sending a partial update like `{"is_completed": true}`
returns `422 Unprocessable Entity` (this is what caused the error seen
earlier in this session).

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

## 3. User passwords are stored and returned in plaintext

`src/user/controller.py` stores whatever string is sent as `hashed_password`
directly — nothing actually hashes it. `get_user()` then returns that value
straight in the API response. Right now, **any client calling `/user/all_user`
gets every password back in plaintext.**

**Fix:**
- Hash on the way in (e.g. with `passlib` or `bcrypt`) inside `create_user`,
  never store/trust a pre-hashed value from the client.
- Add a response schema (separate from the input DTO) that excludes
  `hashed_password` from what gets returned.

## 4. No duplicate/`IntegrityError` handling on user creation

`username` and `email` are `unique=True` at the DB level, but
`create_user` never catches the resulting `IntegrityError` — a duplicate
signup currently crashes with a raw 500 error instead of a clean `400`/`409`.

**Fix:** wrap the commit in a try/except and raise an `HTTPException` with a
clear message, same pattern already used for the 404s in `task/controller.py`.

## 5. `db.query(Task).get(task_id)` is deprecated (legacy SQLAlchemy 1.x API)

Used in both `task/controller.py` (`get_one_task`, `update_task`). SQLAlchemy
2.0 deprecates `Query.get()`; the modern equivalent is:
```python
db.get(Task, task_id)
```

## 6. `from sqlalchemy.orm import session` (lowercase) is not the real `Session` type

Both controllers import `session` (lowercase) and use it only as a type hint
(`db: session`). The actual SQLAlchemy session class is `Session` (capital S).
The lowercase `session` is a different internal module, not a type — so this
type hint is misleading and provides no real type-checking benefit, even
though it happens not to crash at runtime.

**Fix:**
```python
from sqlalchemy.orm import Session
def create_task(body: TaskSchema, db: Session):
```

## 7. `.gitignore` has no actual ignore rules

The file only contains a comment. As a result `.env`, `env/`, and
`__pycache__/` all show up as **untracked** in `git status` instead of being
silently ignored — meaning someone could accidentally `git add .` and commit
real DB credentials.

**Fix — add these lines to `.gitignore`:**
```
.env
env/
__pycache__/
*.pyc
```

## 8. No version pins in `requirement.txt`

None of the five dependencies have a version (e.g. `fastapi==0.115.0`).
A future `pip install -r requirement.txt` could pull breaking major-version
updates without warning.

**Fix:** run `pip freeze > requirement.txt` once your environment is in a
known-good state, or at minimum pin major versions (`fastapi>=0.110,<0.120`).
Also consider renaming the file to the conventional `requirements.txt`
(plural) — most tooling/tutorials assume that name.

## 9. No `DELETE` endpoints, despite comments implying full CRUD

Both `task/controller.py` and `user/router.py` have top comments saying
"read, delete, update, create," but no delete route/function exists for
either resource, and no update/get-by-id exists for users at all.

## 10. `FastAPI(title="his is my task management application ")`

Typo in `main.py:11` — missing the "T" in "This", plus a trailing space.
Purely cosmetic (shows on the `/docs` page title), but easy to fix:
```python
app = FastAPI(title="This is my task management application")
```
