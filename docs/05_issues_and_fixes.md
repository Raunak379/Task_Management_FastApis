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

## 14. 🚨 Hardcoded real SMTP credentials in `src/utils/mail.py`

```python
conf = ConnectionConfig(
    MAIL_USERNAME = "sherraunaksingh@gmail.com",
    MAIL_PASSWORD = "ftkl ewtt mpsw ncry",      ### that is App password not mail password
    ...
)
```

Every other secret in this project (`SECRET_KEY`, `DB_CONNECTION`) is kept in
`.env` and loaded through `src/utils/settings.py`. This one is a real Gmail
address and app password typed directly into a source file instead. Combined
with issue #7 (`.gitignore` has no real rules), this credential is one
`git add .` / `git add -A` away from being pushed to a remote repository.

**Fix:**
1. Add to `.env`:
   ```
   MAIL_USERNAME = "sherraunaksingh@gmail.com"
   MAIL_PASSWORD = "<app password>"
   MAIL_FROM = "sherraunaksingh@gmail.com"
   ```
2. Add matching fields to `src/utils/settings.py`'s `settings` class.
3. In `src/utils/mail.py`, build `ConnectionConfig` from `settings.MAIL_*`
   instead of literal strings.
4. **Rotate/revoke this Gmail app password now** — it has already been
   written into a file (and possibly viewed/shared) and should be treated as
   compromised regardless of whether it ever reaches git.

## 15. `send_email` is called with a list where it expects a single address

`src/utils/mail.py::send_email(email: str)` does `recipients=[email]`
internally — it expects a single address and wraps it itself. But
`src/user/controller.py::register` calls:
```python
bg_task.add_task(send_email, [new_user.email])
```
passing a **one-item list**, not a string. That makes `recipients =
[[new_user.email]]` — a list containing a list — instead of
`recipients = ["new_user@example.com"]`. Since this runs as a background
task (after the HTTP response is already sent), the failure won't show up
in the API response at all, only in server logs/console.

**Fix:**
```python
bg_task.add_task(send_email, new_user.email)
```

## 16. Dead/commented code left in `register()`

```python
##send mail conformation
#res = await send_email(new_user.email)
bg_task.add_task(send_email, [new_user.email])
#print(res)
```
Leftover from an earlier version that `await`ed `send_email` directly
(blocking the response) before switching to `BackgroundTasks`. Harmless but
should be deleted now that the background-task version is the real
implementation.

## 17. `requirement.txt` still doesn't list `fastapi-mail` / `aiosmtplib`

Building on issue #8: `src/utils/mail.py` imports `fastapi_mail`, which
pulls in `aiosmtplib` under the hood (both are installed in `env/`, neither
is in `requirement.txt`). A clean install would now fail at
`ModuleNotFoundError: No module named 'fastapi_mail'` the moment
`/user/register` is hit, on top of the already-missing `PyJWT`/`pwdlib`.

**Fix:** add `fastapi-mail` to `requirement.txt` alongside the fixes in
issue #8.

## 18. `userSchema.email` is typed `str`, not `EmailStr`

`src/user/dtos.py` — `email: str` accepts any string at all, including
obviously-invalid addresses like `"not-an-email"`. Now that this value is
actually used to send mail (`src/utils/mail.py`), a malformed address will
only fail much later, inside the background email task, instead of at
request validation time.

**Fix:**
```python
from pydantic import BaseModel, EmailStr

class userSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
```
