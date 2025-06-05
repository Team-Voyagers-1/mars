# stories/urls.py
from django.urls import path
from .views import SaveRoleConfigView, SaveSubtaskConfigView, SaveFieldConfigView

urlpatterns = [
    path("role-config/", SaveRoleConfigView.as_view(), name="save_role_config"),
    path("subtask-config/", SaveSubtaskConfigView.as_view(), name="save_subtask_config"),
    path("field-config/", SaveFieldConfigView.as_view(), name="save_field_config")
]
