# task-manager (Week 9 starter)

COMP.4600/5300 AI Agents with Claude Code. Starter code for the Week 9 drills.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    pytest -q

## API

| Method | Path | What it does |
| --- | --- | --- |
| GET | /tasks | List tasks. Optional query parameters: status, priority |
| POST | /tasks | Create a task. JSON body: title (required), description, priority, due_date |
| GET | /tasks/<id> | Get one task |
| PATCH | /tasks/<id> | Update fields of a task |
| POST | /tasks/<id>/complete | Mark a task as finished |
| DELETE | /tasks/<id> | Delete a task |
| GET | /stats | Counts by status, completion rate, overdue count |
