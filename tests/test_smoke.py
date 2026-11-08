"""A few end-to-end checks that the app starts and the main routes answer."""


def test_list_tasks_starts_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_task_returns_201(client):
    response = client.post("/tasks", json={"title": "Write report"})
    assert response.status_code == 201
    assert response.get_json()["title"] == "Write report"


def test_missing_title_returns_400(client):
    response = client.post("/tasks", json={})
    assert response.status_code == 400
    assert "title" in response.get_json()["error"]
