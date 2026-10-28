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


def test_get_task_not_found():
    response = client.get("/tasks/99999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_create_task_empty_title():
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "description": "This task has an invalid title"
        }
    )

    assert response.status_code == 422


def test_update_task():
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


def test_delete_task():
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
