#controller.py is used to organize the logic that handles API requests. It becomes useful when your FastAPI project gets bigger.
from src.user.dtos import userSchema
from sqlalchemy.orm import session
from src.user.models import user

#post method
def create_user(body:userSchema, db:session):
    #print(body.model_dump())
    data = body.model_dump()
    new_user = user(username = data["username"],
                    email = data["email"],
                    hashed_password = data["hashed_password"])
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return{"status":"user created successfully...", "data" : new_user}

#get method
def get_user(db:session):
    users = db.query(user).all()
    return{"status":"all task", "data":users}