from sqlalchemy import Boolean, Column, Integer, String
from database import engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
