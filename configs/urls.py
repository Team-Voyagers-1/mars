# stories/urls.py
from django.urls import path
from .views import SaveRoleConfigView, SaveSubtaskConfigView

urlpatterns = [
    path("role-config/", SaveRoleConfigView.as_view(), name="save_role_config"),
    path("subtask-config/", SaveSubtaskConfigView.as_view(), name="save_subtask_config"),
]
