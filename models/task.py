import json
from models.database import get_db


class TestCase:
    @staticmethod
    def list():
        db = get_db()
        rows = db.execute("SELECT * FROM test_cases ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(case_id):
        db = get_db()
        row = db.execute("SELECT * FROM test_cases WHERE id = ?", (case_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name, module="", description="", params="{}"):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO test_cases (name, module, description, params) VALUES (?, ?, ?, ?)",
            (name, module, description, params if isinstance(params, str) else json.dumps(params)),
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def delete(case_id):
        db = get_db()
        db.execute("DELETE FROM test_cases WHERE id = ?", (case_id,))
        db.commit()

    @staticmethod
    def import_cases(cases):
        db = get_db()
        ids = []
        for c in cases:
            cursor = db.execute(
                "INSERT INTO test_cases (name, module, description, params) VALUES (?, ?, ?, ?)",
                (
                    c.get("name", ""),
                    c.get("module", ""),
                    c.get("description", ""),
                    json.dumps(c.get("params", {})),
                ),
            )
            ids.append(cursor.lastrowid)
        db.commit()
        return ids


class Task:
    @staticmethod
    def list():
        db = get_db()
        rows = db.execute(
            "SELECT t.*, s.name as server_name FROM tasks t LEFT JOIN servers s ON t.server_id = s.id ORDER BY t.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(task_id):
        db = get_db()
        row = db.execute(
            "SELECT t.*, s.name as server_name FROM tasks t LEFT JOIN servers s ON t.server_id = s.id WHERE t.id = ?",
            (task_id,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name, test_case_ids):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO tasks (name, test_case_ids) VALUES (?, ?)",
            (name, json.dumps(test_case_ids)),
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(task_id, **kwargs):
        db = get_db()
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "server_id", "result", "started_at", "finished_at"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        vals.append(task_id)
        db.execute(
            f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?",
            vals,
        )
        db.commit()

    @staticmethod
    def delete(task_id):
        db = get_db()
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()

    @staticmethod
    def get_pending():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
