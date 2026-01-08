from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "occupation_db")
COLLECTION_NAME = "translations_cache"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_cached_translation(text, target_lang):
    entry = collection.find_one({"text": text, "lang": target_lang})
    return entry["translation"] if entry else None

def cache_translation(text, target_lang, translation):
    collection.update_one(
        {"text": text, "lang": target_lang},
        {"$set": {"translation": translation}},
        upsert=True
    )
