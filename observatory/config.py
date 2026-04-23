import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

DB_URL = os.getenv("DB_URL", "sqlite:///./project_hide.db")
