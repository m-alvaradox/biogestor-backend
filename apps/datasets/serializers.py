from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer

from .models import Dataset


class DatasetListSerializer(serializers.ModelSerializer):
    owner = UserSummarySerializer(read_only=True)

    class Meta:
        model = Dataset
        fields = ["id", "name", "type", "status", "owner", "created_at"]


class DatasetStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ["s3_uri", "file_format", "size_bytes", "file_count"]


class DatasetDetailSerializer(DatasetListSerializer):
    storage = DatasetStorageSerializer(source="*", read_only=True)

    class Meta(DatasetListSerializer.Meta):
        fields = DatasetListSerializer.Meta.fields + [
            "species",
            "farm",
            "pool",
            "capture_date",
            "type_metadata",
            "storage",
        ]
