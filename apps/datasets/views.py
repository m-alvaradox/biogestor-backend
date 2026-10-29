from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Dataset
from .pagination import DatasetPagination
from .serializers import DatasetListSerializer


class DatasetListView(ListAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetListSerializer
    permission_classes = [AllowAny]
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
