"""Regression test for BUG-17: completed tasks don't count as completed."""


def test_bug17_completed_task_counts_in_stats_and_status_filter(client):
    """Completing a task is reflected in /stats and in GET /tasks?status=completed."""
    # Step 1
    resp = client.post("/tasks", json={"title": "Write report"})
    assert resp.status_code == 201
    assert resp.get_json()["id"] == 1

    # Step 2
    resp = client.post("/tasks", json={"title": "Buy milk"})
    assert resp.status_code == 201
    assert resp.get_json()["id"] == 2

    # Step 3
    resp = client.post("/tasks/1/complete")
    assert resp.status_code == 200

    # Step 4
    stats = client.get("/stats").get_json()
    assert stats["completed"] == 1
    assert stats["completion_rate"] == 50.0

    # Step 5
    resp = client.get("/tasks?status=completed")
    assert resp.status_code == 200
    assert [t["id"] for t in resp.get_json()] == [1]
