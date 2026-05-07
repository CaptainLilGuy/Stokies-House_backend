from django.db import models
from users.models import User
import uuid

class Household(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=8, unique=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_households')
    members = models.ManyToManyField(User, related_name='households', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name