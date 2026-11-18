from rest_framework.generics import ListAPIView

from .models import User
from .serializers import UserListSerializer


class UserListView(ListAPIView):
    queryset = User.objects.filter(status=User.UserStatus.ACTIVE).order_by("name")
    serializer_class = UserListSerializer
    pagination_class = None
