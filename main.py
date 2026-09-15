from fastapi import FastAPI
from database import engine
from fastapi import FastAPI, Depends
from database import engine, get_db
from models import Base, Task
from schemas import TaskCreate

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Task management API is running!"}


@app.get("/test-db")
def test_database(db=Depends(get_db)):
    return {"message": "Database connection successful!"}


@app.post("/tasks")
def create_task(task: TaskCreate, db=Depends(get_db)):
    new_task = Task(
        title=task.title,
        description=task.description
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@app.get("/tasks")
def get_tasks(db=Depends(get_db)):
    tasks = db.query(Task).all()

    return tasks
