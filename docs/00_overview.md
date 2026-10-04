# Task Management FastAPI — Documentation Index

This `docs/` folder explains every file and folder in this project, the concepts
behind them, and how everything connects and runs together.

## What this project is

A small REST API, built with **FastAPI**, for managing `Task` and `user` records
in a **MySQL** database via **SQLAlchemy** (ORM) and **Pydantic** (validation).

## Tech stack

| Tool | Role |
|---|---|
| FastAPI | web framework — defines HTTP routes, handles requests/responses |
| Uvicorn | ASGI server that actually runs FastAPI |
| SQLAlchemy | ORM — maps Python classes to SQL tables, builds/executes queries |
| PyMySQL | the actual MySQL driver SQLAlchemy uses under the hood |
| Pydantic / pydantic-settings | data validation (request bodies) and settings/env loading |

## Reading order

1. `01_folder_structure.md` — map of every file/folder and its one-line purpose
2. `02_concepts.md` — the underlying concepts (FastAPI, Pydantic, SQLAlchemy, DI, env vars)
3. `03_file_by_file.md` — deep line-by-line explanation of every file
4. `04_how_to_run.md` — setup, running the server, connecting to MySQL, testing endpoints
5. `05_issues_and_fixes.md` — bugs/typos found in the current code and how to fix them
