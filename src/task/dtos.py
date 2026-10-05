#data transfer objects, it use be validation of data suppose if user login they should pass username or password, email address, name etc
from pydantic import BaseModel

class TaskSchema(BaseModel):
    title : str
    description : str
    is_completed : bool = False

class TaskResponseSchema(BaseModel):
    id : int
    title : str
    description : str
    is_completed : bool