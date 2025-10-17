import os
from django.apps import AppConfig
from django.conf import settings


class FileManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "file_management"
    path = os.path.join(settings.BASE_DIR, "file_management")
