from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import User
from .serializers import UserSummarySerializer


class UserListView(ListAPIView):
    queryset = User.objects.filter(status=User.UserStatus.ACTIVE).order_by("name")
    serializer_class = UserSummarySerializer
    permission_classes = [AllowAny]
    pagination_class = None
