#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests

BASE_URL = os.environ.get("SRM_URL", "http://127.0.0.1:5000")


def cmd_submit_task(args):
    case_ids = [int(x) for x in args.case_ids.split(",")]
    resp = requests.post(
        f"{BASE_URL}/api/tasks/",
        json={"name": args.name, "test_case_ids": case_ids},
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"Task created: id={data['id']}, message={data['message']}")


def cmd_list_tasks(args):
    resp = requests.get(f"{BASE_URL}/api/tasks/")
    resp.raise_for_status()
    tasks = resp.json()
    for t in tasks:
        status = t["status"]
        server = t.get("server_name") or "auto"
        print(f"  [#{t['id']}] {t['name']}  status={status}  server={server}  created={t['created_at']}")


def cmd_task_result(args):
    resp = requests.get(f"{BASE_URL}/api/tasks/{args.task_id}")
    resp.raise_for_status()
    task = resp.json()
    print(f"Task #{task['id']}: {task['name']}")
    print(f"Status: {task['status']}")
    if task.get("result"):
        r = task["result"] if isinstance(task["result"], dict) else json.loads(task["result"])
        print(f"Result: {r['summary']['passed']}/{r['summary']['total']} passed")
        for d in r.get("details", []):
            mark = "PASS" if d["passed"] else "FAIL"
            print(f"  [{mark}] {d['test_case']} @ {d['server']} ({d['duration_ms']}ms)")
            if d.get("error"):
                print(f"       Error: {d['error']}")
    else:
        print("No result yet.")


def cmd_list_servers(args):
    resp = requests.get(f"{BASE_URL}/api/servers/")
    resp.raise_for_status()
    servers = resp.json()
    for s in servers:
        enabled = "enabled" if s["enabled"] else "DISABLED"
        print(f"  [#{s['id']}] {s['name']} ({s['host']}:{s['port']})  status={s['status']}  {enabled}")


def cmd_import_cases(args):
    with open(args.file) as f:
        data = json.load(f)
    resp = requests.post(f"{BASE_URL}/api/test-cases/import", json=data)
    resp.raise_for_status()
    r = resp.json()
    print(f"Imported {r['imported']} test cases, ids={r['ids']}")


def main():
    parser = argparse.ArgumentParser(description="SRM CLI Client")
    parser.add_argument("--url", default=None, help="SRM server URL (default: $SRM_URL or http://127.0.0.1:5000)")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("submit", help="Submit a test task")
    p.add_argument("--name", required=True, help="Task name")
    p.add_argument("--case-ids", required=True, help="Comma-separated test case IDs")
    p.set_defaults(func=cmd_submit_task)

    p = sub.add_parser("tasks", help="List all tasks")
    p.set_defaults(func=cmd_list_tasks)

    p = sub.add_parser("result", help="Get task result")
    p.add_argument("task_id", type=int)
    p.set_defaults(func=cmd_task_result)

    p = sub.add_parser("servers", help="List servers")
    p.set_defaults(func=cmd_list_servers)

    p = sub.add_parser("import", help="Import test cases from JSON file")
    p.add_argument("file", help="JSON file path")
    p.set_defaults(func=cmd_import_cases)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    if args.url:
        global BASE_URL
        BASE_URL = args.url.rstrip("/")

    try:
        args.func(args)
    except requests.ConnectionError:
        print("Error: Cannot connect to SRM server. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
