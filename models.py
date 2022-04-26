import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class Chat(models.Model):
    name = models.CharField(max_length=200, default="", blank=True)
    object_id = models.CharField(max_length=255)
    object_type = models.CharField(max_length=1000)
    participants = models.ManyToManyField(get_user_model(), blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_changed = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name if self.name else self.id

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ["last_changed"]


class Message(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="messages")
    have_read = models.ManyToManyField(get_user_model(), blank=True, related_name="read_messages")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField()
    created_time = models.DateTimeField(auto_now_add=True)
    changed_time = models.DateTimeField(default=None, null=True)
    changed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.chat.last_changed = timezone.now()
        self.chat.save()
        return super(Message, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created"]


class MessageMedia(models.Model):
    def upload_message_media_file(self, filename):
        return os.path.join("chats", str(self.message.chat.pk), "media", filename)

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to=upload_message_media_file)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename

    class Meta:
        verbose_name = "Медиафайл"
        verbose_name_plural = "Медиафайлы"
