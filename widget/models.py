from django.db import models
from django.utils.text import slugify
from mongoengine import Document, StringField, ListField, DictField


class FeatureDetails(Document):
    name = StringField(required=True)
    handle = StringField(required=True, unique=True)
    context_file = DictField(required=True)  # Main context file
    story_file = DictField(required=False)   # Optional story sheet
    epic_file = DictField(required=False)    # Optional epic sheet

