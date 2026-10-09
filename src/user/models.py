from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from src.utils.db import Base


class user(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    Mobile = Column(Integer,unique = True, nullable= False)
