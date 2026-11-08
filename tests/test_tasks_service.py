"""Unit tests for app/services/tasks.py."""

from datetime import date

import pytest

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import PRIORITIES, Task, TaskStatus
from app.services import tasks as svc
from app.services.tasks import MAX_TITLE_LENGTH

MISSING_ID = 9999


# --------------------------------------------------------------------------- create_task


class TestCreateTask:
    def test_creates_with_defaults(self, app):
        task = svc.create_task("Buy milk")

        assert task.id is not None
        assert task.title == "Buy milk"
        assert task.description == ""
        assert task.priority == "medium"
        assert task.due_date is None
        assert task.status == TaskStatus.TODO
        assert task.created_at is not None

    def test_persists_to_database(self, app):
        task = svc.create_task("Buy milk")

        assert Task.query.count() == 1
        assert db.session.get(Task, task.id).title == "Buy milk"

    def test_creates_with_all_fields(self, app):
        task = svc.create_task(
            "Write report", description="Quarterly", priority="high", due_date="2026-12-31"
        )

        assert task.title == "Write report"
        assert task.description == "Quarterly"
        assert task.priority == "high"
        assert task.due_date == date(2026, 12, 31)

    def test_strips_title_and_description(self, app):
        task = svc.create_task("  Buy milk  ", description="  two litres \n")

        assert task.title == "Buy milk"
        assert task.description == "two litres"

    def test_non_string_title_is_converted(self, app):
        assert svc.create_task(123).title == "123"

    # Title length boundary

    def test_title_at_max_length_is_accepted(self, app):
        title = "a" * MAX_TITLE_LENGTH
        assert svc.create_task(title).title == title

    def test_title_over_max_length_is_rejected(self, app):
        with pytest.raises(ValidationError, match="at most 120 characters"):
            svc.create_task("a" * (MAX_TITLE_LENGTH + 1))
        assert Task.query.count() == 0

    def test_title_length_is_measured_after_stripping(self, app):
        title = "a" * MAX_TITLE_LENGTH
        assert svc.create_task(f"   {title}   ").title == title

    # Empty / whitespace / None title

    @pytest.mark.parametrize("title", [None, "", "   ", "\t\n "])
    def test_missing_title_is_rejected(self, app, title):
        with pytest.raises(ValidationError, match="title is required"):
            svc.create_task(title)
        assert Task.query.count() == 0

    # Description edge cases

    @pytest.mark.parametrize("description", [None, "", "   "])
    def test_empty_description_becomes_empty_string(self, app, description):
        assert svc.create_task("t", description=description).description == ""

    # Priority

    @pytest.mark.parametrize("priority", PRIORITIES)
    def test_each_valid_priority_is_accepted(self, app, priority):
        assert svc.create_task("t", priority=priority).priority == priority

    @pytest.mark.parametrize("priority", ["urgent", "", "   ", None, "HIGH"])
    def test_invalid_priority_is_rejected(self, app, priority):
        with pytest.raises(ValidationError, match="priority must be one of low, medium, high"):
            svc.create_task("t", priority=priority)
        assert Task.query.count() == 0

    # Due date

    @pytest.mark.parametrize("due_date", [None, ""])
    def test_empty_due_date_is_none(self, app, due_date):
        assert svc.create_task("t", due_date=due_date).due_date is None

    def test_due_date_accepts_date_object(self, app):
        assert svc.create_task("t", due_date=date(2027, 1, 2)).due_date == date(2027, 1, 2)

    @pytest.mark.parametrize("due_date", ["31/12/2026", "2026-13-01", "tomorrow", "   ", 20261231])
    def test_invalid_due_date_is_rejected(self, app, due_date):
        with pytest.raises(ValidationError, match="due_date must be a date in YYYY-MM-DD format"):
            svc.create_task("t", due_date=due_date)
        assert Task.query.count() == 0


# --------------------------------------------------------------------------- get_task


class TestGetTask:
    def test_returns_existing_task(self, app):
        created = svc.create_task("t")

        fetched = svc.get_task(created.id)

        assert fetched.id == created.id
        assert fetched.title == "t"

    def test_missing_task_raises_not_found(self, app):
        with pytest.raises(NotFoundError, match=f"task {MISSING_ID} not found"):
            svc.get_task(MISSING_ID)

    def test_none_id_raises_not_found(self, app):
        with pytest.raises(NotFoundError, match="task None not found"):
            svc.get_task(None)

    def test_deleted_task_raises_not_found(self, app):
        task_id = svc.create_task("t").id
        svc.delete_task(task_id)

        with pytest.raises(NotFoundError):
            svc.get_task(task_id)


# --------------------------------------------------------------------------- list_tasks


@pytest.fixture
def sample_tasks(app):
    """Four tasks with mixed status and priority, created in id order."""
    a = svc.create_task("a", priority="low")
    b = svc.create_task("b", priority="high")
    c = svc.create_task("c", priority="high")
    d = svc.create_task("d", priority="medium")
    svc.update_task(b.id, status=TaskStatus.IN_PROGRESS)
    svc.update_task(c.id, status=TaskStatus.COMPLETED)
    return a, b, c, d


def titles(tasks):
    return [t.title for t in tasks]


class TestListTasks:
    def test_empty_database_returns_empty_list(self, app):
        assert svc.list_tasks() == []

    def test_returns_all_tasks_oldest_first(self, app, sample_tasks):
        assert titles(svc.list_tasks()) == ["a", "b", "c", "d"]

    def test_filters_by_status(self, app, sample_tasks):
        assert titles(svc.list_tasks(status=TaskStatus.TODO)) == ["a", "d"]
        assert titles(svc.list_tasks(status=TaskStatus.IN_PROGRESS)) == ["b"]

    def test_filters_by_priority(self, app, sample_tasks):
        assert titles(svc.list_tasks(priority="high")) == ["b", "c"]

    def test_filters_by_status_and_priority(self, app, sample_tasks):
        assert titles(svc.list_tasks(status=TaskStatus.COMPLETED, priority="high")) == ["c"]

    def test_filter_with_no_matches_returns_empty_list(self, app, sample_tasks):
        assert svc.list_tasks(status=TaskStatus.DONE) == []

    @pytest.mark.parametrize("status", ["finished", "", "   ", "TODO"])
    def test_invalid_status_is_rejected(self, app, status):
        with pytest.raises(ValidationError, match="status must be one of"):
            svc.list_tasks(status=status)

    @pytest.mark.parametrize("priority", ["urgent", "", "   "])
    def test_invalid_priority_is_rejected(self, app, priority):
        with pytest.raises(ValidationError, match="priority must be one of"):
            svc.list_tasks(priority=priority)


# --------------------------------------------------------------------------- update_task


class TestUpdateTask:
    def test_updates_all_fields(self, app):
        task = svc.create_task("old")

        updated = svc.update_task(
            task.id,
            title="new",
            description="details",
            priority="high",
            due_date="2027-03-04",
            status=TaskStatus.IN_PROGRESS,
        )

        assert updated.id == task.id
        assert updated.title == "new"
        assert updated.description == "details"
        assert updated.priority == "high"
        assert updated.due_date == date(2027, 3, 4)
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_update_is_persisted(self, app):
        task_id = svc.create_task("old").id
        svc.update_task(task_id, title="new")

        db.session.expire_all()
        assert svc.get_task(task_id).title == "new"

    def test_only_given_fields_change(self, app):
        task = svc.create_task("t", description="keep", priority="low", due_date="2027-01-01")

        svc.update_task(task.id, title="changed")

        assert task.description == "keep"
        assert task.priority == "low"
        assert task.due_date == date(2027, 1, 1)
        assert task.status == TaskStatus.TODO

    def test_no_fields_is_a_no_op(self, app):
        task = svc.create_task("t")
        assert svc.update_task(task.id).title == "t"

    def test_strips_title_and_description(self, app):
        task = svc.create_task("t")

        svc.update_task(task.id, title="  new  ", description="  d  ")

        assert task.title == "new"
        assert task.description == "d"

    @pytest.mark.parametrize("description", [None, "", "   "])
    def test_empty_description_clears_it(self, app, description):
        task = svc.create_task("t", description="something")
        assert svc.update_task(task.id, description=description).description == ""

    @pytest.mark.parametrize("due_date", [None, ""])
    def test_empty_due_date_clears_it(self, app, due_date):
        task = svc.create_task("t", due_date="2027-01-01")
        assert svc.update_task(task.id, due_date=due_date).due_date is None

    @pytest.mark.parametrize("status", TaskStatus.ALL)
    def test_each_valid_status_is_accepted(self, app, status):
        task = svc.create_task("t")
        assert svc.update_task(task.id, status=status).status == status

    # Title length boundary

    def test_title_at_max_length_is_accepted(self, app):
        task = svc.create_task("t")
        title = "b" * MAX_TITLE_LENGTH
        assert svc.update_task(task.id, title=title).title == title

    def test_title_over_max_length_is_rejected(self, app):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="at most 120 characters"):
            svc.update_task(task.id, title="b" * (MAX_TITLE_LENGTH + 1))

    # Error paths

    @pytest.mark.parametrize("title", [None, "", "   "])
    def test_missing_title_is_rejected(self, app, title):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="title is required"):
            svc.update_task(task.id, title=title)

    @pytest.mark.parametrize("priority", ["urgent", "", None])
    def test_invalid_priority_is_rejected(self, app, priority):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="priority must be one of"):
            svc.update_task(task.id, priority=priority)

    @pytest.mark.parametrize("status", ["finished", "", None])
    def test_invalid_status_is_rejected(self, app, status):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="status must be one of"):
            svc.update_task(task.id, status=status)

    @pytest.mark.parametrize("due_date", ["not-a-date", "2027-02-30", 5])
    def test_invalid_due_date_is_rejected(self, app, due_date):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="due_date must be a date"):
            svc.update_task(task.id, due_date=due_date)

    def test_unknown_field_is_rejected(self, app):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="cannot update field\\(s\\): id"):
            svc.update_task(task.id, id=42)

    def test_multiple_unknown_fields_are_listed_sorted(self, app):
        task = svc.create_task("t")
        with pytest.raises(ValidationError, match="cannot update field\\(s\\): created_at, foo"):
            svc.update_task(task.id, foo=1, created_at="x", title="ok")

    def test_missing_task_raises_not_found(self, app):
        with pytest.raises(NotFoundError, match=f"task {MISSING_ID} not found"):
            svc.update_task(MISSING_ID, title="x")

    def test_unknown_field_is_checked_before_existence(self, app):
        with pytest.raises(ValidationError):
            svc.update_task(MISSING_ID, bogus=1)


# --------------------------------------------------------------------------- complete_task


class TestCompleteTask:
    def test_marks_task_finished(self, app):
        task = svc.create_task("t")

        completed = svc.complete_task(task.id)

        assert completed.id == task.id
        assert completed.status in (TaskStatus.COMPLETED, TaskStatus.DONE)
        assert completed.status != TaskStatus.TODO

    def test_uses_current_completed_status(self, app):
        task = svc.create_task("t")
        assert svc.complete_task(task.id).status == TaskStatus.COMPLETED

    def test_completing_twice_is_idempotent(self, app):
        task = svc.create_task("t")
        first = svc.complete_task(task.id).status
        assert svc.complete_task(task.id).status == first

    def test_leaves_other_fields_untouched(self, app):
        task = svc.create_task("t", description="d", priority="high")
        svc.complete_task(task.id)
        assert (task.title, task.description, task.priority) == ("t", "d", "high")

    def test_missing_task_raises_not_found(self, app):
        with pytest.raises(NotFoundError, match=f"task {MISSING_ID} not found"):
            svc.complete_task(MISSING_ID)


# --------------------------------------------------------------------------- delete_task


class TestDeleteTask:
    def test_deletes_task(self, app):
        task_id = svc.create_task("t").id

        assert svc.delete_task(task_id) is None
        assert Task.query.count() == 0

    def test_only_deletes_the_given_task(self, app):
        keep = svc.create_task("keep")
        drop = svc.create_task("drop")

        svc.delete_task(drop.id)

        assert titles(svc.list_tasks()) == ["keep"]
        assert svc.get_task(keep.id).title == "keep"

    def test_missing_task_raises_not_found(self, app):
        with pytest.raises(NotFoundError, match=f"task {MISSING_ID} not found"):
            svc.delete_task(MISSING_ID)

    def test_deleting_twice_raises_not_found(self, app):
        task_id = svc.create_task("t").id
        svc.delete_task(task_id)

        with pytest.raises(NotFoundError):
            svc.delete_task(task_id)
