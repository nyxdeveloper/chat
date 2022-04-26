from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Chat
from .models import Message
from .models import MessageMedia


class ParticipantSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    avatar = serializers.ImageField()

    class Meta:
        model = get_user_model()
        fields = ["id", "name", "avatar"]


class ChatSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True)
    unread_count = serializers.SerializerMethodField()

    def get_unread_count(self, instance):
        if len(self.context):
            instance.messages.exclude(have_read=self.context["request"].user).count()
        return 0

    class Meta:
        model = Chat
        fields = ["id", "name", "object_id", "object_type", "participants"]


class MessageMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageMedia
        field = ["id", "filename", "file"]


class MessageSerializer(serializers.ModelSerializer):
    user = ParticipantSerializer(many=False)
    read = serializers.SerializerMethodField()
    media = MessageMediaSerializer(many=True)

    def get_read(self, instance):
        if len(self.context):
            return self.context["request"].user.read_messages.filter(pk=instance.pk).exists()
        return False

    class Meta:
        model = Message
        fields = ["id", "user", "read", "chat", "text", "created_time", "changed_time", "changed", "media"]
