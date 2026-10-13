#controller.py is used to organize the logic that handles API requests. It becomes useful when your FastAPI project gets bigger.
from fastapi import HTTPException, status
from src.user.dtos import userSchema, LoginSchema
from sqlalchemy.orm import Session
from src.user.models import user
from pwdlib import PasswordHash
from src.utils.settings import settings
from datetime import datetime, timedelta
import jwt

password_hash = PasswordHash.recommended()
def get_password_hash(password):
    return password_hash.hash(password)
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


##### REGISTER USER----------
def register(body:userSchema, db:Session):
    #print(body)
    ##1. usersname validation
    is_user = db.query(user).filter(user.username == body.username).first()
    if is_user:
        raise HTTPException(400, detail= "user already exist...")
    
    ##2. Email validation
    is_user = db.query(user).filter(user.email == body.email).first()
    if is_user:
        raise HTTPException(400, detail = "email address already exist...")
    
    ##3 password hash
    hash_password = get_password_hash(body.password)
    ##4 create object for user
    new_user = user(
        username = body.username,
        email = body.email,
        hashed_password = hash_password,

    )
    ##5 store the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



##### LOGIN USER------
def login_user(body, db:Session):
    ##print(body)
    ##verify username 
    is_user = db.query(user).filter(user.username == body.username).first()
    if not is_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you are entered wrong password")
    ##verify password
    if not verify_password(body.password, is_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you are entered wrong password")

    ##genrate token for user throug jwt
    exp_time = datetime.now()+timedelta(minutes=settings.EXP_TIME)
    print(exp_time)
    token = jwt.encode({"username":is_user.username, "exp":exp_time}, settings.SECRET_KEY, settings.ALGORITHM)
    return {"token":token}