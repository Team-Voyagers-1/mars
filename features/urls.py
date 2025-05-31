from django.urls import path
from .views import FeatureView

urlpatterns = [
    path('', FeatureView.as_view()),
]