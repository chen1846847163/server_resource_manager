import json
import logging
import threading
import time
from datetime import datetime

from models.server import Server
from models.task import Task
from mock.mock_test_runner import run_mock_test

logger = logging.getLogger(__name__)

_scheduler_thread = None
_stop_event = threading.Event()
SCHEDULER_INTERVAL = 3


def _schedule_loop():
    logger.info("Scheduler started")
    while not _stop_event.is_set():
        try:
            pending = Task.get_pending()
            for task in pending:
                available = Server.get_available()
                if not available:
                    logger.warning("No available servers for task %s", task["id"])
                    continue

                busy_server_ids = set()
                running = [t for t in Task.list() if t["status"] == "running"]
                for rt in running:
                    if rt["server_id"]:
                        busy_server_ids.add(rt["server_id"])

                target_server = None
                for s in available:
                    if s["id"] not in busy_server_ids:
                        target_server = s
                        break

                if target_server is None:
                    target_server = available[0]

                Task.update(
                    task["id"],
                    status="running",
                    server_id=target_server["id"],
                    started_at=datetime.now().isoformat(),
                )

                thread = threading.Thread(
                    target=_execute_task, args=(task, target_server), daemon=True
                )
                thread.start()

        except Exception as e:
            logger.error("Scheduler error: %s", e)

        _stop_event.wait(SCHEDULER_INTERVAL)
    logger.info("Scheduler stopped")


def _execute_task(task, server):
    logger.info("Executing task %s on server %s", task["id"], server["name"])
    case_ids = json.loads(task["test_case_ids"])
    results = []
    for cid in case_ids:
        from models.task import TestCase

        tc = TestCase.get(cid)
        if not tc:
            results.append({"test_case": f"unknown_id_{cid}", "passed": False, "error": "Test case not found"})
            continue
        r = run_mock_test(tc["name"], server, tc.get("params"))
        results.append(r)

    passed_count = sum(1 for r in results if r.get("passed"))
    final_status = "completed" if passed_count == len(results) else "failed"

    Task.update(
        task["id"],
        status=final_status,
        result=json.dumps({"summary": {"total": len(results), "passed": passed_count, "failed": len(results) - passed_count}, "details": results}, ensure_ascii=False),
        finished_at=datetime.now().isoformat(),
    )
    logger.info("Task %s finished: %s", task["id"], final_status)


def start_scheduler():
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_schedule_loop, daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    _stop_event.set()
