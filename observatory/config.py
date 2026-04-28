import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

DB_URL = os.getenv("DB_URL", f"sqlite:///{BASE_DIR / 'project_hide.db'}")
