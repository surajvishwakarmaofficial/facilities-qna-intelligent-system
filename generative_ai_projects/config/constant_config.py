import os
from dotenv import load_dotenv
import pathlib

load_dotenv()

class Config:

    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
    SQLITE_DB_URL = os.environ.get("SQLITE_DB_URL")

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    AUTO_ESCALATION_SCHEDULAR = os.environ.get("AUTO_ESCALATION_SCHEDULAR", 5) #5 minutes

    PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
    KNOWLEDGE_BASE_DIR = "./data/knowledge_base_files"
    
    #milvus config
    MILVUS_DATABASE = os.environ.get("MILVUS_DATABASE", "")
    MILVUS_HOST = os.environ.get("MILVUS_HOST", "")
    MILVUS_PORT = os.environ.get("MILVUS_PORT", "")
    MILVUS_COLLECTION_NAME = os.environ.get("MILVUS_COLLECTION_NAME", "")

    #aws s3 config
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
    AWS_REGION = os.environ.get("AWS_REGION", "")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

    
