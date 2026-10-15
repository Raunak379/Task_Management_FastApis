from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql import func

from src.utils.db import Base


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    user_id = Column(Integer, ForeignKey("user.id",ondelete="CASCADE"))

## send the user_id in payload
