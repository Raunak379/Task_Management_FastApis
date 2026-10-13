#data transfer objects, it use be validation of data suppose if user login they should pass username or password, email address, name etc
from pydantic import BaseModel

##### REGISTER USER----
class userSchema(BaseModel):
    username : str
    email : str
    password: str

## it can use for hide password
class userResponseSchema(BaseModel):
    username : str
    email : str
    id : int


##### LOGIN USER-----
class LoginSchema(BaseModel):
    username : str
    password : str
    