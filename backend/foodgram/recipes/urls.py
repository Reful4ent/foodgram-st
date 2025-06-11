from django.urls import path
from api import views

urlpatterns = [path('recipes/',
                    views.RecipesViewSet.as_view({'get': 'list'}),
                    name='recipes-list')
               ]