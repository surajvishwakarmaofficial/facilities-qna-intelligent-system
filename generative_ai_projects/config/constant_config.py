
import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

class Config:

    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
    SQLITE_DB_URL = os.environ.get("SQLITE_DB_URL")
    COLLECTION_NAME = os.environ.get("COLLECTION_NAME")

    MILVUS_URI = os.environ.get("MILVUS_URI")
    MILVUS_TOKEN = os.environ.get("MILVUS_TOKEN")

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

    