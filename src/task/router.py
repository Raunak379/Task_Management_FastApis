#if you can talk about user so, it can be read, delete, update, create.
from fastapi import APIRouter,Depends
from src.task import controller
from src.task.dtos import TaskSchema
from src.utils.db import get_db
task_routes = APIRouter(prefix= "/task")    #prefix =  https://127.0.0.1:8000/prefix/route

#post method
@task_routes.post("/create")
def create_task(body:TaskSchema, db = Depends(get_db)):
    return controller.create_task(body, db)

#get method
@task_routes.get("/all_task")
def get_all_task(db = Depends(get_db)):
    return controller.get_task(db)

#get specific data with the help of id, number etc
@task_routes.get("/one_task/{task_id}")
def get_one_task(task_id:int, db = Depends(get_db)):
    return controller.get_one_task(task_id, db)

#update the task
@task_routes.put("/update_task/{task_id}")
def update_task(body:TaskSchema,task_id:int,db = Depends(get_db)):
    return controller.update_task(body, task_id, db)

#delete task
@task_routes.delete("/delete_task/{task_id}")
def delete_task(task_id:int,db = Depends(get_db)):
    return controller.delete_task(task_id, db)