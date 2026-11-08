"""Characterization tests for app/services/stats.py and the GET /stats route.

These pin down the current behavior of task_summary so it can be refactored safely.
"""

from datetime import date, timedelta

import pytest

from app.extensions import db
from app.models import Task, TaskStatus
from app.services import stats as stats_module
from app.services.stats import task_summary

TODAY = date(2026, 6, 15)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


def add_task(title="Task", status=TaskStatus.TODO, due_date=None):
    """Insert a task directly into the database and return it."""
    task = Task(title=title, status=status, due_date=due_date)
    db.session.add(task)
    db.session.commit()
    return task


# --------------------------------------------------------------------------- empty database


def test_empty_database(app):
    assert task_summary(today=TODAY) == {
        "total": 0,
        "todo": 0,
        "in_progress": 0,
        "completed": 0,
        "overdue": 0,
        "completion_rate": 0.0,
    }


# --------------------------------------------------------------------------- status counts


def test_counts_todo(app):
    add_task(status=TaskStatus.TODO)
    add_task(status=TaskStatus.TODO)

    result = task_summary(today=TODAY)

    assert result["total"] == 2
    assert result["todo"] == 2
    assert result["in_progress"] == 0
    assert result["completed"] == 0


def test_counts_in_progress(app):
    add_task(status=TaskStatus.IN_PROGRESS)

    result = task_summary(today=TODAY)

    assert result["total"] == 1
    assert result["todo"] == 0
    assert result["in_progress"] == 1
    assert result["completed"] == 0


def test_counts_completed(app):
    add_task(status=TaskStatus.COMPLETED)

    result = task_summary(today=TODAY)

    assert result["total"] == 1
    assert result["todo"] == 0
    assert result["in_progress"] == 0
    assert result["completed"] == 1
    assert result["completion_rate"] == 100.0


def test_counts_mixed_statuses(app):
    add_task(status=TaskStatus.TODO)
    add_task(status=TaskStatus.TODO)
    add_task(status=TaskStatus.IN_PROGRESS)
    add_task(status=TaskStatus.COMPLETED)

    result = task_summary(today=TODAY)

    assert result["total"] == 4
    assert result["todo"] == 2
    assert result["in_progress"] == 1
    assert result["completed"] == 1
    assert result["completion_rate"] == 25.0


def test_legacy_done_status_counts_only_toward_total(app):
    # Current behavior: the legacy "done" value is not counted as completed.
    add_task(status=TaskStatus.DONE)

    result = task_summary(today=TODAY)

    assert result["total"] == 1
    assert result["todo"] == 0
    assert result["in_progress"] == 0
    assert result["completed"] == 0
    assert result["completion_rate"] == 0.0


# --------------------------------------------------------------------------- completion rate


def test_completion_rate_rounds_to_one_decimal(app):
    add_task(status=TaskStatus.COMPLETED)
    add_task(status=TaskStatus.TODO)
    add_task(status=TaskStatus.TODO)

    assert task_summary(today=TODAY)["completion_rate"] == 33.3


# --------------------------------------------------------------------------- overdue


@pytest.mark.parametrize(
    ("due_date", "status", "expected"),
    [
        pytest.param(YESTERDAY, TaskStatus.TODO, 1, id="due-yesterday"),
        pytest.param(YESTERDAY, TaskStatus.IN_PROGRESS, 1, id="due-yesterday-in-progress"),
        pytest.param(TODAY, TaskStatus.TODO, 0, id="due-today"),
        pytest.param(TOMORROW, TaskStatus.TODO, 0, id="due-tomorrow"),
        pytest.param(None, TaskStatus.TODO, 0, id="no-due-date"),
        pytest.param(YESTERDAY, TaskStatus.COMPLETED, 0, id="past-due-but-completed"),
        pytest.param(YESTERDAY, TaskStatus.DONE, 1, id="past-due-legacy-done"),
    ],
)
def test_overdue_rules(app, due_date, status, expected):
    add_task(status=status, due_date=due_date)

    assert task_summary(today=TODAY)["overdue"] == expected


def test_overdue_counts_across_tasks(app):
    add_task(due_date=YESTERDAY)
    add_task(due_date=TODAY - timedelta(days=30))
    add_task(due_date=TODAY)
    add_task(due_date=TOMORROW)
    add_task(due_date=None)
    add_task(status=TaskStatus.COMPLETED, due_date=YESTERDAY)

    assert task_summary(today=TODAY)["overdue"] == 2


# --------------------------------------------------------------------------- default today


class FakeDate(date):
    """date subclass whose today() returns the fixed TODAY."""

    @classmethod
    def today(cls):
        return TODAY


def test_default_today_uses_date_today(app, monkeypatch):
    monkeypatch.setattr(stats_module, "date", FakeDate)
    add_task(due_date=YESTERDAY)
    add_task(due_date=TODAY)

    assert task_summary()["overdue"] == 1


# --------------------------------------------------------------------------- GET /stats


def test_stats_route_empty(client):
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.get_json() == {
        "total": 0,
        "todo": 0,
        "in_progress": 0,
        "completed": 0,
        "overdue": 0,
        "completion_rate": 0.0,
    }


def test_stats_route_returns_summary(client, monkeypatch):
    monkeypatch.setattr(stats_module, "date", FakeDate)
    add_task(status=TaskStatus.TODO, due_date=YESTERDAY)
    add_task(status=TaskStatus.IN_PROGRESS)
    add_task(status=TaskStatus.COMPLETED, due_date=YESTERDAY)

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.get_json() == {
        "total": 3,
        "todo": 1,
        "in_progress": 1,
        "completed": 1,
        "overdue": 1,
        "completion_rate": 33.3,
    }
