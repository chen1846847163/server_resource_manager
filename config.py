import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "srm.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")

HOST = os.environ.get("SRM_HOST", "0.0.0.0")
PORT = int(os.environ.get("SRM_PORT", 5000))
DEBUG = os.environ.get("SRM_DEBUG", "true").lower() == "true"

os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
