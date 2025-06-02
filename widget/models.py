from django.db import models
from django.utils.text import slugify
from mongoengine import Document, StringField, ListField, DictField


class FeatureDetails(Document):
    name = StringField(required=True)
    handle = StringField(required=True, unique=True)
    details = ListField(DictField())

