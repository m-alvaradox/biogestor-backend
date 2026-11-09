from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.users.models import User
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
        extra_kwargs = {"s3_uri": {"validators": []}}


class DatasetCreateSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    storage = DatasetStorageSerializer(source="*", required=False)

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "type",
            "status",
            "owner",
            "created_at",
            "description",
            "species",
            "farm",
            "pool",
            "capture_date",
            "license",
            "type_metadata",
            "storage",
        ]

        read_only_fields = ["id", "created_at"]

    def validate_capture_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("La fecha de captura no puede ser futura.")

        return value

    def validate(self, attrs):
        s3_uri = attrs.get("s3_uri")
        if s3_uri:
            duplicates = Dataset.objects.filter(s3_uri=s3_uri)
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError(
                    {"storage": {"s3_uri": ["Ya existe un dataset con esta referencia de S3."]}}
                )

        return attrs

    def create(self, validated_data):
        dataset = Dataset(**validated_data)

        try:
            dataset.full_clean()
        except DjangoValidationError as error:
            if hasattr(error, "message_dict"):
                raise serializers.ValidationError(error.message_dict) from error

            raise serializers.ValidationError({"non_field_errors": error.messages}) from error

        dataset.save()
        return dataset


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


class DatasetUpdateSerializer(DatasetCreateSerializer):
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.full_clean()
        except DjangoValidationError as error:
            if hasattr(error, "message_dict"):
                raise serializers.ValidationError(error.message_dict) from error

            raise serializers.ValidationError({"non_field_errors": error.messages}) from error

        instance.save()
        return instance
