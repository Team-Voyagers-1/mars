from pymongo import MongoClient
from django.conf import settings
from mongoengine import connect
import gridfs

connect(settings.MONGO_DB_NAME)

client = MongoClient(settings.MONGO_URI)
mongo_db = client[settings.MONGO_DB_NAME]

fs = gridfs.GridFS(mongo_db)
