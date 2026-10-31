from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None
    due_date: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    completed: bool | None = None
    due_date: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    completed: bool
    due_date: str | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
