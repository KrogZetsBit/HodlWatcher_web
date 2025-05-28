from django.contrib import admin

from .models import (
    Configuracion,
    InvestmentWatchdog,
    UsuarioTelegram,
    WatchdogNotification,
)


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


@admin.register(InvestmentWatchdog)
class InvestmentWatchdogAdmin(admin.ModelAdmin):
    list_display = ["user", "currency", "side", "amount", "created_at"]
    search_fields = ["user__username", "currency"]
    list_filter = ["side", "currency"]
    ordering = ["-created_at"]
    list_per_page = 50
    list_max_show_all = 100
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "currency",
                    "side",
                    "amount",
                    "active",
                )
            },
        ),
    )


@admin.register(WatchdogNotification)
class WatchdogNotificationAdmin(admin.ModelAdmin):
    list_display = ["watchdog", "offer_id", "notified_at", "is_active"]
    search_fields = ["watchdog__user__username", "offer_id"]
    list_filter = ["notified_at"]
    ordering = ["-notified_at"]
    list_per_page = 50
    list_max_show_all = 100
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "watchdog",
                    "offer_id",
                    "notified_at",
                    "is_active",
                )
            },
        ),
    )
