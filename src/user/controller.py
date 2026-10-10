#controller.py is used to organize the logic that handles API requests. It becomes useful when your FastAPI project gets bigger.
from fastapi import HTTPException
from src.user.dtos import userSchema
from sqlalchemy.orm import Session
from src.user.models import user

def register(body:userSchema, db:Session):
    #print(body)
    ##1. usersname validation
    is_user = db.query(user).filter(user.username == body.username).first()
    if is_user:
        raise HTTPException``
    ##2. Email validation

    return{"msg":"registration Done"}