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

This reads every package listed in `requirement.txt` and installs it into
the `env/` virtual environment (not your system Python).

## 4. Configure `.env`

Already present at the project root:
```
DB_CONNECTION = "mysql+pymysql://root:<password>@localhost/task_management"
```
Update the username/password/host/database name to match your own MySQL setup.
`src/utils/settings.py` reads this automatically on startup — no code changes needed.

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

Both let you fill in a form and send real requests without needing curl or Postman.

### Example requests with `curl`

Create a task:
```bash
curl -X POST http://127.0.0.1:8000/task/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2% milk", "is_completed": false}'
```

Get all tasks:
```bash
curl http://127.0.0.1:8000/task/all_task
```

Get one task:
```bash
curl http://127.0.0.1:8000/task/one_task/1
```

Update a task (remember: **all three fields are currently required** —
see `05_issues_and_fixes.md`):
```bash
curl -X PUT http://127.0.0.1:8000/task/update_task/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "whole milk this time", "is_completed": true}'
```

Create a user:
```bash
curl -X POST http://127.0.0.1:8000/user/create \
  -H "Content-Type: application/json" \
  -d '{"username": "angad", "email": "angad14723@gmail.com", "hashed_password": "temporary"}'
```

## 7. How the pieces connect, end to end

```
MySQL  <-- pymysql driver <-- SQLAlchemy engine (src/utils/db.py)
                                      |
                              LocalSession (per-request DB session)
                                      |
                        get_db() dependency (Depends)
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

`settings.py` feeds the DB connection string (from `.env`) into `db.py` at
import time — that's the one place config and the database layer connect.
