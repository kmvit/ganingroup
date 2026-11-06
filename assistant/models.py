from django.db import models
from django.utils import timezone
import uuid


class KnowledgePage(models.Model):
    site = models.CharField(max_length=12, choices=[('ganin', 'ГАНИН ГРУПП'), ('sd2', 'Стройдеталь-2')])
    url = models.URLField(unique=True)
    title = models.CharField(max_length=250)
    content = models.TextField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['site', 'url']
        verbose_name = 'Страница базы знаний'
        verbose_name_plural = 'Страницы базы знаний'

    def __str__(self):
        return f'{self.get_site_display()}: {self.title}'


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.CharField(max_length=12)
    ip_digest = models.CharField(max_length=64)
    consent_version = models.CharField(max_length=20)
    consent_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Диалог ассистента'
        verbose_name_plural = 'Диалоги ассистента'
        ordering = ['-created_at']


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'Посетитель'), ('assistant', 'Ассистент')])
    text = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
        verbose_name = 'Сообщение ассистента'
        verbose_name_plural = 'Сообщения ассистента'


class DailyIPUsage(models.Model):
    day = models.DateField()
    ip_digest = models.CharField(max_length=64)
    count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['day', 'ip_digest'], name='unique_assistant_ip_day')]
        verbose_name = 'Суточный лимит ассистента'
        verbose_name_plural = 'Суточные лимиты ассистента'
