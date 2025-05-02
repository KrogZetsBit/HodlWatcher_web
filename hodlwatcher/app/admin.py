from django.contrib import admin

from .models import Configuracion
from .models import UsuarioTelegram


@admin.register(UsuarioTelegram)
class UsuarioTelegramAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "username")
    search_fields = ("chat_id", "username")
    ordering = ("chat_id", "username")
    fields = ("chat_id", "username")
    readonly_fields = ("chat_id", "username")
    list_per_page = 50
    list_max_show_all = 100


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ["user", "user_telegram", "image"]
    search_fields = ["user__username"]
    readonly_fields = ["user"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "user_telegram",
                    "image",
                )
            },
        ),
    )
