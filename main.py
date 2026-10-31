from fastapi import FastAPI, Depends, HTTPException, Query
from database import engine
from database import engine, get_db
from models import Base, Task, User
from schemas import TaskCreate, TaskUpdate, TaskResponse, UserCreate, UserResponse
from security import hash_password

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
def get_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="asc", pattern="^(asc|desc)$"),
    db=Depends(get_db)
):
    query = db.query(Task)

    if sort == "asc":
        query = query.order_by(Task.id.asc())
    else:
        query = query.order_by(Task.id.desc())

    tasks = query.offset(skip).limit(limit).all()

    return tasks


@app.get("/tasks/completed", response_model=list[TaskResponse])
def get_completed_tasks(db=Depends(get_db)):
    tasks = db.query(Task).filter(Task.completed == True).all()

    return tasks


@app.get("/tasks/pending", response_model=list[TaskResponse])
def get_pending_tasks(db=Depends(get_db)):
    tasks = db.query(Task).filter(Task.completed == False).all()

    return tasks


@app.get("/tasks/stats")
def get_task_stats(db=Depends(get_db)):
    total = db.query(Task).count()
    completed = db.query(Task).filter(Task.completed == True).count()
    pending = db.query(Task).filter(Task.completed == False).count()

    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }


@app.get("/tasks/search", response_model=list[TaskResponse])
def search_tasks(
    keyword: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db=Depends(get_db)
):
    tasks = (
        db.query(Task)
        .filter(
            (Task.title.ilike(f"%{keyword}%")) |
            (Task.description.ilike(f"%{keyword}%"))
        )
        .order_by(Task.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

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


@app.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserCreate, db=Depends(get_db)):

    existing_user = db.query(User).filter(
        (User.username == user.username) |
        (User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username or email already registered"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
