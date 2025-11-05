from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DownloadJobViewSet

# Create your views here.

router = DefaultRouter()
router.register(r'jobs', DownloadJobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),
]