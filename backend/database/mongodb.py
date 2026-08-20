
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["wms_ai_agent"]

inventory_collection = db["inventory"]