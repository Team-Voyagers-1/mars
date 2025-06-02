# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_feature_details),
    path('feature-details/', views.get_feature_details),
    path('feature-details-filtered/', views.get_feature_details_filtered),
]