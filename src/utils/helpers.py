
from fastapi import Request,HTTPException,status, Depends
from src.utils.settings import settings
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError
from src.user.models import user
from src.utils.db import get_db
import jwt
######  BASE ON TOKEN HOW TO AUTHENTICATE ----- IF USER CALL APIS THAT MEAN SEND THE TOKEN ---- IN HEADER
def is_authenticated(request:Request, db:Session = Depends(get_db)):
    try:
       token = request.headers.get("authorization")
       if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized") 
       token = token.split(" ")[-1]
       data = jwt.decode(token,settings.SECRET_KEY, settings.ALGORITHM)
       user_name = data.get("username")
       #exp_time = data.get("exp")

       #current_time = datetime.now().timestamp()
       #print(exp_time - current_time)
       #if current_time > exp_time:
       #    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
       is_user = db.query(user).filter(user.username == user_name).first()
       if not is_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
       return is_user
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "you are unauthorized")
