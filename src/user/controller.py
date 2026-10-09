#controller.py is used to organize the logic that handles API requests. It becomes useful when your FastAPI project gets bigger.
from src.user.dtos import userSchema
from sqlalchemy.orm import Session

def register(body:userSchema, db:Session):
    print(body)
    return{"msg":"registration Done"}