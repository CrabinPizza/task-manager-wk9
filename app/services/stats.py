"""Summary statistics for the dashboard."""

from collections import Counter
from datetime import date

from app.models import Task, TaskStatus


def task_summary(today=None):
    """Return counts by status, the completion rate, and the number of overdue tasks."""
    if today is None:
        today = date.today()
    tasks = Task.query.all()
    total = len(tasks)

    status_counts = Counter(task.status for task in tasks)
    todo = status_counts[TaskStatus.TODO]
    in_progress = status_counts[TaskStatus.IN_PROGRESS]
    completed = status_counts[TaskStatus.COMPLETED]

    overdue = sum(
        1
        for task in tasks
        if task.due_date is not None
        and task.due_date < today
        and task.status != TaskStatus.COMPLETED
    )

    if total > 0:
        completion_rate = round(100 * completed / total, 1)
    else:
        completion_rate = 0.0

    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "completion_rate": completion_rate,
    }
