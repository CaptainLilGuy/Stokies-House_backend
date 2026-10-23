from django.conf import settings
from django.db import models

class NotificationLog(models.Model):
    class Kind(models.TextChoices):
        EXPIRY_DIGEST = 'expiry_digest', 'Expiry digest'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_logs')
    kind = models.CharField(max_length=30, choices=Kind.choices)
    sent_for = models.DateField()
    title = models.CharField(max_length=200)
    body = models.TextField()
    item_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'kind', 'sent_for'], name='one_digest_per_user_per_day')]