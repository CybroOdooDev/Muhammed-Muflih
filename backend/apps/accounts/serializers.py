from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "picture",
            "is_admin",
        ]
        read_only_fields = fields
