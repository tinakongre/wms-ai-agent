import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set")


client = MongoClient(MONGODB_URI)

db = client["wms_ai_agent"]

inventory_collection = db["inventory"]