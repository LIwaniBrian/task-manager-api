from fastapi import FastAPI, Depends, HTTPException
from database import engine
from database import engine, get_db
from models import Base, Task
from schemas import TaskCreate, TaskUpdate, TaskResponse

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Task management API is running!"}


@app.get("/test-db")
def test_database(db=Depends(get_db)):
    return {"message": "Database connection successful!"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db=Depends(get_db)):
    new_task = Task(
        title=task.title,
        description=task.description
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db=Depends(get_db)):
    tasks = db.query(Task).all()

    return tasks


@app.get("/tasks/completed", response_model=list[TaskResponse])
def get_completed_tasks(db=Depends(get_db)):
    tasks = db.query(Task).filter(Task.completed == True).all()

    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db=Depends(get_db)):
    existing_task = db.query(Task).filter(Task.id == task_id).first()

    if existing_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.title is not None:
        existing_task.title = task.title

    if task.description is not None:
        existing_task.description = task.description

    if task.completed is not None:
        existing_task.completed = task.completed

    db.commit()
    db.refresh(existing_task)

    return existing_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}
