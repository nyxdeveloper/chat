from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q

from .models import Chat
from .models import Message
from .models import MessageMedia

from .serializers import ChatSerializer
from .serializers import MessageSerializer
from .serializers import MessageMediaSerializer

from .pagination import StandardPagination


class ChatViewSet(ModelViewSet):
    queryset = Chat.objects.filter(deleted=False)
    serializer_class = ChatSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ["object_id", "object_type"]
    search_fields = ["name"]

    def get_queryset(self):
        return self.queryset.filter(participants=self.request.user)


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.filter(Q(chat__deleted=False) and Q(deleted=False))
    serializer_class = MessageSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ["chat"]
    search_fields = ["text"]

    def get_queryset(self):
        return self.queryset.filter(chat__participants=self.request.user)


class MessageMediaViewSet(ModelViewSet):
    queryset = MessageMedia.objects.filter(chat__deleted=False)
    serializer_class = MessageMediaSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ["message__chat"]
    search_fields = ["file"]

    def get_queryset(self):
        return self.queryset.filter(message__chat__participants=self.request.user)
