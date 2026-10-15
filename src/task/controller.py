#controller.py is used to organize the logic that handles API requests. It becomes useful when your FastAPI project gets bigger.

from src.task.dtos import TaskSchema
from sqlalchemy.orm import session
from src.task.models import Task
from fastapi import HTTPException
from src.user.models import user

#post method
def create_task(body:TaskSchema, db:session, is_user:user):
    #print(body.model_dump())
    data = body.model_dump()
    new_task = Task(title = data["title"],
                     description = data["description"],
                     is_completed = data["is_completed"],
                     user_id = is_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return{"status":"task create successfully", "data":new_task}

#get method
def get_task(db:session, is_user:user):
    tasks = db.query(Task).filter(Task.user_id == is_user.id).all()
    return{"status":"all task", "data":tasks}

#get specific data with the help of id, number e.t.c
def get_one_task(task_id:int, db:session):
    one_task = db.query(Task).get(task_id)
    if not one_task:
        raise HTTPException(404, detail="task Id is Incorrect")
    return{"status":"Task Fetched Successfully", "data":one_task}

#update the task
def update_task(body:TaskSchema,task_id:int,db:session, is_user:user):
    one_task = db.query(Task).get(task_id)
    if not one_task:
        raise HTTPException(404, detail="task Id is Incorrect")
    #one_task.title = body.title
    #one_task.description = body.description          this is 3 line for updating single line update 
    #one_task.is_completed = body.is_completed

    
    if one_task.user_id != is_user.id:
        raise HTTPException(401, detail="you are not allowed to update this task")

    body = body.model_dump()
    for field, value in body.items():
        setattr(one_task,field,value)

    db.add(one_task)
    db.commit()
    db.refresh(one_task)

    return {"status":"task updated successfully", "data":one_task}


#delete a task
def delete_task(task_id:int,db:session, is_user:user):
    one_task = db.query(Task).get(task_id)
    if not one_task:
        raise HTTPException(404, detail="task Id is Incorrect")
    
    if one_task.user_id != is_user.id:
        raise HTTPException(401, detail="you are not allowed to delete this task")
    
    db.delete(one_task)
    db.commit()

    #return {"status":"task deleted successfully"}
    return None