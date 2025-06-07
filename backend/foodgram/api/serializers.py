from rest_framework import serializers
from ingredients.models import Ingredient
from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.core.files.base import ContentFile
import base64


User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredient

class Base64ImageField(serializers.ImageField):
    
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"avatar.{ext}"
            )
        
        return super().to_internal_value(data)

class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email',
                  'id', 
                  'username',  
                  'first_name', 
                  'last_name',
                  'is_subscribed',
                  'avatar'
        )

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 
                  'email',
                  'username', 
                  'first_name', 
                  'last_name', 
                  'password'
        )