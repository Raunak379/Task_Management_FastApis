#data transfer objects, it use be validation of data suppose if user login they should pass username or password, email address, name etc
from pydantic import BaseModel
class userSchema(BaseModel):
    username : str
    email : str
    hashed_password: str