"""HTTP route for dashboard statistics."""

from flask import Blueprint, jsonify

from app.services.stats import task_summary

bp = Blueprint("stats", __name__, url_prefix="/stats")


@bp.get("")
def stats():
    return jsonify(task_summary())
