from pymongo import MongoClient
import gridfs
from bson import ObjectId
from decouple import config

# Mongo connection setup
client = MongoClient(config("MONGO_URI"))
db = client[config("MONGO_DB_NAME")]
fs = gridfs.GridFS(db)

def fetch_file_by_id(file_id: str) -> bytes:
    """Fetches a file from GridFS using its ObjectId"""
    try:
        grid_out = fs.get(ObjectId(file_id))
        return grid_out.read()
    except Exception as e:
        print(f"Error fetching file: {e}")
        return None

def fetch_file_by_filename(filename: str) -> bytes:
    """Fetches a file by filename (if needed)"""
    try:
        grid_out = fs.find_one({"filename": filename})
        return grid_out.read() if grid_out else None
    except Exception as e:
        print(f"Error: {e}")
        return None
