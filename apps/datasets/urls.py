from django.urls import path

from . import views

urlpatterns = [
    path("datasets/", views.DatasetListView.as_view(), name="dataset-list"),
]
