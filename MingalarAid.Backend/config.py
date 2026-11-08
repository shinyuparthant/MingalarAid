import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "MingalarAid.Frontend"
DATABASE_PATH = BACKEND_DIR / "data" / "mingalar_aid.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret")
