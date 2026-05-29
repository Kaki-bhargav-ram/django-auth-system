from django.db import models
from django.contrib.auth.models import User


class OTP(models.Model):

    PURPOSE_CHOICES = (
        ('register', 'Register'),
        ('login', 'Login'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    otp = models.CharField(max_length=6)

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.purpose}"