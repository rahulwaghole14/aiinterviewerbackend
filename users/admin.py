# users/admin.py
from django.contrib import admin
from rest_framework.authtoken.models import Token

# Prefer TokenProxy when available (DRF >= 3.15 makes Token abstract)
try:
    from rest_framework.authtoken.models import TokenProxy as TokenModel
except ImportError:  # Older DRF
    TokenModel = Token

# Ensure no duplicate registrations
for model in (TokenModel, Token):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


@admin.register(TokenModel)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "user_role", "created")
    search_fields = ("user__email", "key")
    actions = ["delete_selected"]

    def user_role(self, obj):
        return getattr(obj.user, "role", "—")

    user_role.short_description = "Role"
