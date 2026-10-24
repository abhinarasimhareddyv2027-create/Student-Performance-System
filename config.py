import os

from dotenv import load_dotenv
from platformdirs import user_data_path


load_dotenv()

APP_NAME = "StudentPerformanceSystem"
APP_AUTHOR = "StudentPerformanceSystem"
DATA_DIR = user_data_path(APP_NAME, APP_AUTHOR)
DEFAULT_DATABASE_PATH = DATA_DIR / "performance.sqlite3"
DATABASE_URL = os.environ.get(
    "SPS_DATABASE_URL",
    f"sqlite:///{os.environ.get('SPS_DATABASE_PATH', str(DEFAULT_DATABASE_PATH))}",
)