from django.db import models


class Role:
    ADMIN = 'Admin'
    SOURCING_PARTNER = 'Sourcing Partner'

    CHOICES = [
        (ADMIN, 'Admin'),
        (SOURCING_PARTNER, 'Sourcing Partner'),
    ]


class UserData(models.Model):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=Role.CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    permission_granted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.role}"
