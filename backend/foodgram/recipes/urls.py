from django.urls import path
from api import views

#Ничего из api импортировать нельзя!
#Перенесите в это приложение контроллер.
# Мне получается переносить все всювс, сериализаторы и пермишены тоже в приложение? я по другому не могу их разорвать иначе у меня везде будут импорта из api
urlpatterns = [path('recipes/',
                    views.RecipesViewSet.as_view({'get': 'list'}),
                    name='recipes-list')
               ]