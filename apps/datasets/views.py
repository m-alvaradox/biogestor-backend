from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny

from .models import Dataset
from .pagination import DatasetPagination
from .serializers import (
    DatasetCreateSerializer,
    DatasetDetailSerializer,
    DatasetListSerializer,
    DatasetUpdateSerializer,
)


class DatasetViewMixin:
    queryset = Dataset.objects.select_related("owner")
    permission_classes = [AllowAny]


class DatasetListView(DatasetViewMixin, ListCreateAPIView):
    serializer_class = DatasetListSerializer
    pagination_class = DatasetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "species"]
    ordering_fields = ["name", "created_at", "capture_date", "type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        dataset_type = params.get("type")
        if dataset_type:
            if dataset_type not in Dataset.DatasetType.values:
                raise ValidationError({"type": f"Valor no válido: {dataset_type}."})
            queryset = queryset.filter(type=dataset_type)

        status = params.get("status")
        if status:
            if status not in Dataset.Status.values:
                raise ValidationError({"status": f"Valor no válido: {status}."})
            queryset = queryset.filter(status=status)

        owner = params.get("owner")
        if owner:
            if not owner.isdigit():
                raise ValidationError({"owner": "Debe ser un id numérico."})
            queryset = queryset.filter(owner_id=int(owner))

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DatasetCreateSerializer
        return DatasetListSerializer

    def create(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise NotFound("No encontrado.")

        return super().create(request, *args, **kwargs)


class DatasetDetailView(DatasetViewMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = DatasetDetailSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DatasetUpdateSerializer

        return DatasetDetailSerializer

    def update(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise NotFound("No encontrado.")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise NotFound("No encontrado.")

        return super().destroy(request, *args, **kwargs)
