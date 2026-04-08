import json
from flask import Blueprint, request, jsonify
from models.task import Task, TestCase
from mock.mock_test_runner import get_mock_test_cases

bp = Blueprint("tasks", __name__, url_prefix="/api")


@bp.route("/test-cases/", methods=["GET"])
def list_test_cases():
    cases = TestCase.list()
    return jsonify(cases)


@bp.route("/test-cases/<int:case_id>", methods=["GET"])
def get_test_case(case_id):
    tc = TestCase.get(case_id)
    if not tc:
        return jsonify({"error": "Test case not found"}), 404
    return jsonify(tc)


@bp.route("/test-cases/import", methods=["POST"])
def import_test_cases():
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array of test cases"}), 400
    ids = TestCase.import_cases(data)
    return jsonify({"imported": len(ids), "ids": ids}), 201


@bp.route("/test-cases/import-mock", methods=["POST"])
def import_mock_test_cases():
    cases = get_mock_test_cases()
    ids = TestCase.import_cases(cases)
    return jsonify({"imported": len(ids), "ids": ids}), 201


@bp.route("/test-cases/<int:case_id>", methods=["DELETE"])
def delete_test_case(case_id):
    TestCase.delete(case_id)
    return jsonify({"message": "Test case deleted"})


@bp.route("/tasks/", methods=["GET"])
def list_tasks():
    tasks = Task.list()
    for t in tasks:
        if isinstance(t.get("test_case_ids"), str):
            t["test_case_ids"] = json.loads(t["test_case_ids"])
        if isinstance(t.get("result"), str):
            t["result"] = json.loads(t["result"])
    return jsonify(tasks)


@bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    if isinstance(task.get("test_case_ids"), str):
        task["test_case_ids"] = json.loads(task["test_case_ids"])
    if isinstance(task.get("result"), str):
        task["result"] = json.loads(task["result"])
    return jsonify(task)


@bp.route("/tasks/", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    case_ids = data.get("test_case_ids", [])
    if not case_ids:
        return jsonify({"error": "test_case_ids is required (non-empty list)"}), 400
    tid = Task.create(data["name"], case_ids)
    return jsonify({"id": tid, "message": "Task created, waiting to be scheduled"}), 201


@bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    Task.delete(task_id)
    return jsonify({"message": "Task deleted"})


@bp.route("/tasks/<int:task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    task = Task.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    if task["status"] not in ("pending", "running"):
        return jsonify({"error": f"Cannot cancel task in '{task['status']}' state"}), 400
    Task.update(task_id, status="cancelled", finished_at=__import__("datetime").datetime.now().isoformat())
    return jsonify({"message": "Task cancelled"})


@bp.route("/dashboard/", methods=["GET"])
def dashboard():
    servers = __import__("models.server", fromlist=["Server"]).Server.list()
    tasks = Task.list()
    cases = TestCase.list()

    total_servers = len(servers)
    online_servers = sum(1 for s in servers if s["status"] == "online" and s["enabled"])
    disabled_servers = sum(1 for s in servers if not s["enabled"])

    task_stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
    for t in tasks:
        st = t.get("status", "pending")
        if st in task_stats:
            task_stats[st] += 1

    return jsonify(
        {
            "servers": {"total": total_servers, "online": online_servers, "disabled": disabled_servers},
            "tasks": task_stats,
            "test_cases": len(cases),
        }
    )
