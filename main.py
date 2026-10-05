#Then main.py becomes the starting point of your application, while routes, database logic, models, etc. are separated into their own files.

from fastapi import FastAPI
from src.utils.db import Base, engine
#from src.task.models import task_models
#from src.user.models import user_models
from src.task.router import task_routes
from src.user.router import user_routes

Base.metadata.create_all(engine)
app = FastAPI(title = "this is my task management application ")
app.include_router(task_routes)
app.include_router(user_routes)
