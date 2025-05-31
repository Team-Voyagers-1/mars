# stories/urls.py
from django.urls import path
from .views import GenerateStoriesView

urlpatterns = [
    path("generate-stories/", GenerateStoriesView.as_view(), name="generate_stories"),
]
