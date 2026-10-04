#if you can talk about user so, it can be read, delete, update, create.
from fastapi import APIRouter, Depends
from src.user import controller
from src.user.dtos import userSchema
from src.utils.db import get_db

user_routes = APIRouter(prefix="/user")

#post method
@user_routes.post("/create")
def create_user(body:userSchema, db = Depends(get_db)):
    return controller.create_user(body,db)

#get method
@user_routes.get("/all_user")
def get_all_task(db = Depends(get_db)):
    return controller.get_user(db)