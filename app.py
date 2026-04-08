import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from flask_cors import CORS
from models.database import init_db
from scheduler.scheduler import start_scheduler
from api.servers import bp as servers_bp
from api.tasks import bp as tasks_bp
from config import HOST, PORT, DEBUG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def create_app():
    app = Flask(__name__)
    CORS(app)

    init_db()

    app.register_blueprint(servers_bp)
    app.register_blueprint(tasks_bp)

    @app.route("/")
    def page_dashboard():
        return render_template("dashboard.html", page="dashboard")

    @app.route("/servers")
    def page_servers():
        return render_template("servers.html", page="servers")

    @app.route("/test-cases")
    def page_test_cases():
        return render_template("test_cases.html", page="cases")

    @app.route("/tasks")
    def page_tasks():
        return render_template("tasks.html", page="tasks")

    return app


if __name__ == "__main__":
    app = create_app()
    start_scheduler()
    logging.info("Starting SRM server on %s:%s", HOST, PORT)
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
