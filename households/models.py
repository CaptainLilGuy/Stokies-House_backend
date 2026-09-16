from django.db import models
from users.models import User
import uuid

class Household(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=8, unique=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_households')
    members = models.ManyToManyField(User, through='HouseholdMember', related_name='households', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class HouseholdMember(models.Model):
    OWNER = 'owner'
    MEMBER = 'member'
    ROLE_CHOICES = [(OWNER, 'Owner'), (MEMBER, 'Member')]

    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('household', 'user')