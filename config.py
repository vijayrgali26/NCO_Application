import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "occupation_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "reports")
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
