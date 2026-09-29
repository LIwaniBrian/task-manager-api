from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Task management API is running!"
    }


def test_create_task():
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


def test_get_tasks():
    response = client.get("/tasks")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_get_task():
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
