from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework.utils import json

# локальные импорты
from .models import Chat


class ChatConsumer(WebsocketConsumer):
    queryset = Chat.objects.all()

    def get_queryset(self):
        return self.queryset.filter(participants=self.scope["user"])

    def get_object(self):
        try:
            return self.get_queryset().get(id=self.scope['url_route']['kwargs']['pk'])
        except self.queryset.model.DoesNotExist:
            return None

    def connect(self):
        try:
            self.chat = self.get_object()
            if self.chat:
                if self.chat.participants.filter(id=self.scope["user"].id).exists():
                    self.room_name = self.chat.id
                    self.room_group_name = f'chat-{self.room_name}'
                    async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
                    self.accept()
        except Chat.DoesNotExist:
            self.disconnect(404)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': text_data_json["type"],
                'message': message
            }
        )

    def chat_message(self, event):
        # message = Message.objects.create(
        #     user=self.scope["user"],
        #     chat=self.chat,
        #     **event['message']
        # )
        # # Send message to WebSocket
        # serializer = MessageSerializer(Message.objects.get(id=message.id))
        # text_data = json.dumps({
        #     "type": "chat_message",
        #     "message": serializer.data
        # }, cls=encoders.JSONEncoder, ensure_ascii=False)
        # self.send(text_data=text_data)
        # for participant in message.chat.participants.exclude(id=message.user.id).values_list("id", flat=True):
        #     async_to_sync(self.channel_layer.group_send)(
        #         f"messages-{participant}",
        #         {"type": "chat_message", "message": text_data}
        #     )
        self.send(text_data=event["message"])

        # Receive message from room group

    def read_messages(self, event):
        self.send(text_data=event["message"])


class MessageConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope["user"]
        self.room_name = f"messages-{self.user.pk}"
        self.room_group_name = self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': text_data_json["type"],
                'message': message
            }
        )

    def new_message(self, event):
        self.send(text_data=event["message"])
