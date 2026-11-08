"""HTTP routes for tasks. Thin: parse the request, call a service, return JSON."""

from flask import Blueprint, jsonify, request

from app.services import tasks as task_service

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@bp.get("")
def list_tasks():
    status = request.args.get("status")
    priority = request.args.get("priority")
    tasks = task_service.list_tasks(status=status, priority=priority)
    return jsonify([t.to_dict() for t in tasks])


@bp.get("/search")
def search_tasks():
    """Return tasks matching the q query parameter, newest first."""
    tasks = task_service.search_tasks(request.args.get("q"))
    return jsonify([t.to_dict() for t in tasks])


@bp.post("")
def create_task():
    data = request.get_json(silent=True) or {}
    task = task_service.create_task(
        title=data.get("title"),
        description=data.get("description", ""),
        priority=data.get("priority", "medium"),
        due_date=data.get("due_date"),
    )
    return jsonify(task.to_dict()), 201


@bp.get("/<int:task_id>")
def get_task(task_id):
    return jsonify(task_service.get_task(task_id).to_dict())


@bp.patch("/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    return jsonify(task_service.update_task(task_id, **data).to_dict())


@bp.post("/<int:task_id>/complete")
def complete_task(task_id):
    return jsonify(task_service.complete_task(task_id).to_dict())


@bp.delete("/<int:task_id>")
def delete_task(task_id):
    task_service.delete_task(task_id)
    return "", 204
