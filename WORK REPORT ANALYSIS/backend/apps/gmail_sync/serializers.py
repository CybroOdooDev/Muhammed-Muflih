from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Project
        fields = ["id", "name", "emails", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_emails(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("emails must be a list.")
        cleaned = [e.strip().lower() for e in value if isinstance(e, str) and e.strip()]
        return cleaned
