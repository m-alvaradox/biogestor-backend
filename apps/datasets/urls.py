from django.urls import path

from . import views

urlpatterns = [
    path("datasets/", views.DatasetListView.as_view(), name="dataset-list"),
    path("datasets/<int:pk>/", views.DatasetDetailView.as_view(), name="dataset-detail"),
]
