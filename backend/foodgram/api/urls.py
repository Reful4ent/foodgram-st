from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet
)
from rest_framework import routers
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path("", include(router.urls)),
    path("", include("djoser.urls")),
]
