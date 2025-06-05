# stories/urls.py
from django.urls import path
from .views import GenerateStoriesView, GenerateEpicsView, GetStoriesView, UpdateJiraView

urlpatterns = [
    path("generate-stories/", GenerateStoriesView.as_view(), name="generate_stories"),
    path("generate-epics/", GenerateEpicsView.as_view(), name="generate_epics"),
    path("get-stories/", GetStoriesView.as_view(), name="get_stories"),
    path("update-jira/", UpdateJiraView.as_view(), name="update_jira"),
]
