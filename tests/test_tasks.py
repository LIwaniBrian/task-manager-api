import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from models import Base, User
from security import hash_password, create_access_token


TEST_DATABASE_URL = "sqlite:///./test_tasks.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create a test user
    db = TestingSessionLocal()

    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("TestPassword123")
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    # Generate a JWT token for the test user
    token = create_access_token(
        data={"sub": str(test_user.id)}
    )

    db.close()

    try:
        with TestClient(app) as test_client:
            test_client.headers.update({
                "Authorization": f"Bearer {token}"
            })

            yield test_client

    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Task management API is running!"
    }


def test_create_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Test task",
            "description": "Created by automated test"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test task"
    assert data["description"] == "Created by automated test"
    assert data["completed"] is False


def test_get_tasks(client):
    response = client.get("/tasks")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_get_task(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Task for GET test",
            "description": "Testing one task"
        }
    )

    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == "Task for GET test"
    assert data["description"] == "Testing one task"


def test_get_task_not_found(client):
    response = client.get("/tasks/99999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_create_task_empty_title(client):
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "description": "This task has an invalid title"
        }
    )

    assert response.status_code == 422


def test_update_task(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original title",
            "description": "Original description"
        }
    )

    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Updated title",
            "description": "Updated description",
            "completed": True
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated title"
    assert data["description"] == "Updated description"
    assert data["completed"] is True


def test_delete_task(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Task to delete",
            "description": "This task will be deleted"
        }
    )

    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Task deleted successfully"
    }

    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 404


def test_get_tasks_pagination(client):
    for number in range(3):
        client.post(
            "/tasks",
            json={
                "title": f"Pagination task {number}",
                "description": "Testing pagination"
            }
        )

    response = client.get("/tasks?skip=1&limit=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Pagination task 1"


def test_get_tasks_sorting(client):
    for number in range(3):
        client.post(
            "/tasks",
            json={
                "title": f"Sorting task {number}",
                "description": "Testing sorting"
            }
        )

    response = client.get("/tasks?sort=desc")

    assert response.status_code == 200

    data = response.json()

    assert data[0]["title"] == "Sorting task 2"
    assert data[1]["title"] == "Sorting task 1"
    assert data[2]["title"] == "Sorting task 0"


def test_search_tasks_by_description(client):
    client.post(
        "/tasks",
        json={
            "title": "University work",
            "description": "Complete Python programming exercises"
        }
    )

    response = client.get("/tasks/search?keyword=Python")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "University work"
