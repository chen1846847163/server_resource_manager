from flask import Blueprint, request, jsonify
from models.server import Server

bp = Blueprint("servers", __name__, url_prefix="/api/servers")


@bp.route("/", methods=["GET"])
def list_servers():
    enabled_only = request.args.get("enabled_only", "0") == "1"
    servers = Server.list(enabled_only=enabled_only)
    return jsonify(servers)


@bp.route("/<int:server_id>", methods=["GET"])
def get_server(server_id):
    server = Server.get(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404
    return jsonify(server)


@bp.route("/", methods=["POST"])
def create_server():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("host"):
        return jsonify({"error": "name and host are required"}), 400
    sid = Server.create(data["name"], data["host"], data.get("port", 22), data.get("tags", ""))
    return jsonify({"id": sid, "message": "Server created"}), 201


@bp.route("/<int:server_id>", methods=["PUT"])
def update_server(server_id):
    server = Server.get(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    Server.update(server_id, **data)
    return jsonify({"message": "Server updated"})


@bp.route("/<int:server_id>/toggle", methods=["POST"])
def toggle_server(server_id):
    server = Server.get(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404
    new_enabled = 0 if server["enabled"] else 1
    Server.update(server_id, enabled=new_enabled)
    return jsonify({"id": server_id, "enabled": bool(new_enabled), "message": f"Server {'enabled' if new_enabled else 'disabled'}"})


@bp.route("/<int:server_id>", methods=["DELETE"])
def delete_server(server_id):
    Server.delete(server_id)
    return jsonify({"message": "Server deleted"})
