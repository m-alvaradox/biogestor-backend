from rest_framework import serializers

from .models import Dataset


class DatasetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ["id", "name", "type", "status", "owner", "created_at"]
