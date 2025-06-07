from .views import CustomUserViewSet
from rest_framework import routers
from django.urls import path, include
from rest_framework.authtoken import views

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path("", include(router.urls)),
    path("", include("djoser.urls")),
]