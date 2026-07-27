import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/data/langue.db")
DATABASE_PATH = "/app/data/langue.db"
DATA_DIR = "/app/data"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
LANGUE_FILES_DIR = "/app/langue_files"
