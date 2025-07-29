# users/admin.py
from django.contrib import admin
from rest_framework.authtoken.models import Token

# DRF 3.15+ includes a proxy; import safely
try:
    from rest_framework.authtoken.models import TokenProxy
except ImportError:
    TokenProxy = None


# ── 1.  Remove DRF’s default registration of TokenProxy (if it exists) ──────
if TokenProxy:
    try:
        admin.site.unregister(TokenProxy)
    except admin.sites.NotRegistered:
        pass

# ── 2.  Remove any earlier registration of Token (defensive) ───────────────
try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass


# ── 3.  Register Token with a four‑column admin (includes delete) ──────────
@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display  = ("key", "user", "user_role", "created")
    search_fields = ("user__email", "key")
    actions       = ["delete_selected"]   # checkboxes + bulk delete

    def user_role(self, obj):
        return getattr(obj.user, "role", "—")
    user_role.short_description = "Role"
