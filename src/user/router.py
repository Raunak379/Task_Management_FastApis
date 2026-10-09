#if you can talk about user so, it can be read, delete, update, create.
from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from src.user import controller
from src.user.dtos import userSchema
from src.utils.db import get_db

user_routes = APIRouter(prefix="/user")

#post method
@user_routes.post("/register", status_code=status.HTTP_201_CREATED)
def register(body:userSchema, db:Session = Depends(get_db)):
    return controller.register(body,db)