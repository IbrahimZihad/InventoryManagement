from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom user model that extends AbstractUser with profile fields
    and enforces a unique, required email address. Uses CustomUserManager
    for user/superuser creation.
    """

    email = models.EmailField("email address", unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.username
