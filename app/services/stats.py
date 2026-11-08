"""Summary statistics for the dashboard."""

from datetime import date

from app.models import Task, TaskStatus


def task_summary(today=None):
    """Return counts by status, the completion rate, and the number of overdue tasks."""
    if today is None:
        today = date.today()
    tasks = Task.query.all()
    total = len(tasks)

    todo = 0
    for task in tasks:
        if task.status == TaskStatus.TODO:
            todo += 1

    in_progress = 0
    for task in tasks:
        if task.status == TaskStatus.IN_PROGRESS:
            in_progress += 1

    completed = 0
    for task in tasks:
        if task.status == TaskStatus.COMPLETED:
            completed += 1

    overdue = 0
    for task in tasks:
        if task.due_date is not None and task.due_date < today:
            if task.status != TaskStatus.COMPLETED:
                overdue += 1

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
