# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_feature_details),
    path('feature-details/', views.get_feature_details),
    path('all-features/', views.get_all_features),
    path('update_feature/', views.update_feature),
    path('validate-epic/', views.validate_uploaded_epic_file),
    path('validate-story/', views.validate_uploaded_story_file),
]