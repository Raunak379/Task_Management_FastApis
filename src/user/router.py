#if you can talk about user so, it can be read, delete, update, create.
from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from src.user import controller
from src.user.dtos import userSchema, userResponseSchema, LoginSchema
from src.utils.db import get_db

user_routes = APIRouter(prefix="/user")
##### REGISTER USER----

#post method                    #hide password
@user_routes.post("/register", response_model = userResponseSchema, status_code=status.HTTP_201_CREATED)
def register(body:userSchema, db:Session = Depends(get_db)):
    return controller.register(body,db)

##### LOGIN USER-----
@user_routes.post("/login",status_code=status.HTTP_200_OK)
def login(body:LoginSchema, db:Session=Depends(get_db)):
    return controller.login_user(body,db)