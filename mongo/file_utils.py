from pymongo import MongoClient
import gridfs
from bson import ObjectId
from decouple import config

# Mongo connection setup
client = MongoClient(config("MONGO_URI"))
db = client[config("MONGO_DB_NAME")]
fs = gridfs.GridFS(db)

def fetch_file_by_id(file_id: ObjectId):
    """Fetches a file from GridFS using its ObjectId"""
    try:
        file_obj = fs.get(file_id)
        return {
             "data": file_obj.read(),  # bytes
             "filename": file_obj.filename,
             "content_type": file_obj.content_type
        }

    except gridfs.errors.NoFile:
            raise FileNotFoundError("File not found in GridFS")
    except Exception as e:
            raise RuntimeError(f"Error retrieving file: {str(e)}")

def fetch_file_by_filename(filename: str) -> bytes:
    """Fetches a file by filename (if needed)"""
    try:
        grid_out = fs.find_one({"filename": filename})
        return grid_out.read() if grid_out else None
    except Exception as e:
        print(f"Error: {e}")
        return None
