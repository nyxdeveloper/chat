from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.utils import json, encoders

from django.db.models import Q
from django.db import transaction
from django.conf import settings

from .models import Chat
from .models import Message
from .models import MessageMedia

from .serializers import ChatSerializer
from .serializers import MessageSerializer
from .serializers import MessageMediaSerializer

from .pagination import StandardPagination

from pyfcm import FCMNotification

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
push_service = FCMNotification(api_key=settings.FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"])


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

    def filter_queryset(self, queryset):
        queryset = super(MessageViewSet, self).filter_queryset(queryset)
        queryset.exclude(user=self.request.user).update(read=True)
        new_reads = list(queryset.exclude(readers=self.request.user).values_list("id", flat=True))
        # self.request.user.read_messages.add(*list(queryset.values_list("id", flat=True)))
        self.request.user.read_messages.add(*new_reads)
        chat_id = self.request.query_params.get("chat")
        if len(new_reads) and chat_id:
            data = {
                "user": self.request.user.id,
                "messages": new_reads
            }
            async_to_sync(channel_layer.group_send)(
                f"chat-{chat_id}",
                {"type": "read_messages", "message": json.dumps(data, cls=encoders.JSONEncoder, ensure_ascii=False)}
            )
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
        message = serializer.instance
        chat_data = ChatSerializer(message.chat).data
        message_data = serializer.data
        message_text_data = json.dumps(message_data, cls=encoders.JSONEncoder, ensure_ascii=False)
        message_cut_text = message.cut_text
        message_chat_id = message.chat_id
        message_chat_object_id = message.chat.object_id
        message_chat_object_type = message.chat.object_type
        async_to_sync(channel_layer.group_send)(
            f"chat-{message.chat_id}", {"type": "chat_message", "message": message_text_data}
        )
        async_to_sync(channel_layer.group_send)(
            f"messages-{self.request.user.pk}", {"type": "new_message", "message": message_text_data}
        )
        for participant in message.chat.participants.filter(is_active=True):
            push_service.notify_topic_subscribers(
                message_title=message.user.name,
                badge=Message.get_unread_count(participant),
                topic_name=str(participant.pk),
                message_body=message_cut_text,
                sound="default",
                extra_notification_kwargs={
                    "push_type": "message",
                    "chat_id": message_chat_id,
                    "chat_object_id": message_chat_object_id,
                    "chat_object_type": message_chat_object_type,
                    "chat": chat_data
                }
            )


class MessageMediaViewSet(ModelViewSet):
    queryset = MessageMedia.objects.filter(chat__deleted=False)
    serializer_class = MessageMediaSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ["message__chat"]
    search_fields = ["file"]

    def get_queryset(self):
        return self.queryset.filter(message__chat__participants=self.request.user)
