from django.shortcuts import redirect
from .models import Recipe
from rest_framework.response import Response
from rest_framework import status


def short_link_redirect(request, recipe_id): 
    recipe_exists = Recipe.objects.filter(id=recipe_id).exists()
    if recipe_exists:
        return redirect(f'/recipes/{recipe_id}/')
    return Response(
        {'error': 'Рецепт не существует!'},
        status=status.HTTP_400_BAD_REQUEST
    )
