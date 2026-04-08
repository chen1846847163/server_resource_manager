import json
from models.database import get_db


class Server:
    @staticmethod
    def list(enabled_only=False):
        db = get_db()
        if enabled_only:
            rows = db.execute(
                "SELECT * FROM servers WHERE enabled = 1 ORDER BY id"
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM servers ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(server_id):
        db = get_db()
        row = db.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name, host, port=22, tags=""):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO servers (name, host, port, tags) VALUES (?, ?, ?, ?)",
            (name, host, port, tags),
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(server_id, **kwargs):
        db = get_db()
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("name", "host", "port", "status", "enabled", "tags"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        vals.append(server_id)
        db.execute(
            f"UPDATE servers SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            vals,
        )
        db.commit()

    @staticmethod
    def delete(server_id):
        db = get_db()
        db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
        db.commit()

    @staticmethod
    def get_available():
        db = get_db()
        rows = db.execute(
            "SELECT * FROM servers WHERE enabled = 1 AND status = 'online' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
