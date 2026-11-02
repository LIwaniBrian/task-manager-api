from fastapi import FastAPI, Depends, HTTPException, Query
from database import engine
from database import engine, get_db
from models import Base, Task, User
from schemas import TaskCreate, TaskUpdate, TaskResponse, UserCreate, UserResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from security import hash_password, create_access_token, verify_password, verify_access_token

app = FastAPI()

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scheme_name="JWT"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db)
):
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@app.get("/users/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


@app.get("/")
def home():
    return {"message": "Task management API is running!"}


@app.get("/test-db")
def test_database(db=Depends(get_db)):
    return {"message": "Database connection successful!"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        owner_id=current_user.id
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
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task).filter(
        Task.owner_id == current_user.id
    )

    if sort == "asc":
        query = query.order_by(Task.id.asc())
    else:
        query = query.order_by(Task.id.desc())

    tasks = query.offset(skip).limit(limit).all()

    return tasks


@app.get("/tasks/completed", response_model=list[TaskResponse])
def get_completed_tasks(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tasks = db.query(Task).filter(
        Task.completed == True,
        Task.owner_id == current_user.id
    ).all()

    return tasks


@app.get("/tasks/pending", response_model=list[TaskResponse])
def get_pending_tasks(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Task).filter(
        Task.completed == False,
        Task.owner_id == current_user.id
    ).all()

    return tasks


@app.get("/tasks/stats")
def get_task_stats(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task).filter(
        Task.owner_id == current_user.id
    )

    total = query.count()

    completed = query.filter(
        Task.completed == True
    ).count()

    pending = query.filter(
        Task.completed == False
    ).count()

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
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tasks = (
        db.query(Task)
        .filter(
            Task.owner_id == current_user.id,
            (
                (Task.title.ilike(f"%{keyword}%")) |
                (Task.description.ilike(f"%{keyword}%"))
            )
        )
        .order_by(Task.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if existing_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if task.title is not None:
        existing_task.title = task.title

    if task.description is not None:
        existing_task.description = task.description

    if task.completed is not None:
        existing_task.completed = task.completed

    if task.due_date is not None:
        existing_task.due_date = task.due_date

    db.commit()
    db.refresh(existing_task)

    return existing_task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

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


@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db)
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
