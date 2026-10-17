#if you can talk about user so, it can be read, delete, update, create.
from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from src.user import controller
from src.user.dtos import userSchema, userResponseSchema, LoginSchema
from src.utils.db import get_db

user_routes = APIRouter(prefix="/user")
##### REGISTER USER----

#post method                    #hide password
@user_routes.post("/register", response_model = userResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(body:userSchema, bg_task:BackgroundTasks, db:Session = Depends(get_db)):
    return await controller.register(body,db, bg_task)

##### LOGIN USER-----
@user_routes.post("/login",status_code=status.HTTP_200_OK)
def login(body:LoginSchema, db:Session=Depends(get_db)):
    return controller.login_user(body,db)

######  BASE ON TOKEN HOW TO AUTHENTICATE ----- IF USER CALL APIS THAT MEAN SEND THE TOKEN ---- IN HEADER
        ###get method
@user_routes.get("/is_auth",status_code=status.HTTP_200_OK,response_model= userResponseSchema)
def is_auth(request:Request, db:Session = Depends(get_db)):
    return controller.is_authenticated(request,db)