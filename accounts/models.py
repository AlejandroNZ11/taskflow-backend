from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario personalizado: email único y una bio opcional."""

    email = models.EmailField("correo electrónico", unique=True)
    bio = models.TextField("biografía", blank=True)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.username
