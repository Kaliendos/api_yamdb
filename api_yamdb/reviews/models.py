from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    bio = models.TextField(
        "Биография",
        blank=True
    )
    ROLE_CHOICES = (
        ("user" , "user" ),
        ("admin", "admin"),
        ("moderator", "moderator"),
    )

    role = models.CharField(
        max_length=150,
        choices=ROLE_CHOICES,
        default="user")


class Review(models.Model):
    text = models.TextField()