import uuid

from django.core.validators import RegexValidator
from django.db import models

from hodlwatcher.users.models import User


class UsuarioTelegram(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    recibir_alertas_watchdog = models.BooleanField(default=False)
    rate_fee = models.FloatField(default=0.0)

    # Puedes añadir una relación inversa a InvestmentWatchdog si lo deseas
    # Esto permite acceder directamente a los watchdogs desde el usuario de Telegram

    def __str__(self):
        return self.username or f"ID: {self.chat_id}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Your Name")
    email = models.EmailField(verbose_name="Email Address")
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,17}$",
        message="Phone number must be entered in the format: '+99999999999'. Up to 15 digits allowed.",
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name="Phone Number")
    subject = models.CharField(max_length=200, verbose_name="Subject")
    message = models.TextField(verbose_name="Your Message")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class Configuracion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_telegram = models.OneToOneField(UsuarioTelegram, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to="profile_pics/", default="profile.png")

    def __str__(self):
        return f"Config for {self.user.username}"


class InvestmentWatchdog(models.Model):
    SIDE_CHOICES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchdogs")
    currency = models.CharField(max_length=3, default="EUR")
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default="sell")
    rate_fee = models.DecimalField("Rate Fee (%)", max_digits=4, decimal_places=2, default=0)
    payment_method_id = models.CharField(max_length=6, default="51")
    amount = models.PositiveIntegerField()
    asset_code = models.CharField(max_length=3, default="BTC")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    usuario_telegram = models.ForeignKey(
        UsuarioTelegram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="watchdogs",
    )

    class Meta:
        verbose_name = "Watchdog"
        verbose_name_plural = "Watchdogs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Watchdog de {self.user.email} - {self.currency}"


class WatchdogNotification(models.Model):
    watchdog = models.ForeignKey(InvestmentWatchdog, on_delete=models.CASCADE, related_name="notifications")
    offer_id = models.CharField(max_length=100)
    notified_at = models.DateTimeField(auto_now_add=True)
    offer_details = models.JSONField(blank=True, null=True)  # Guarda detalles importantes de la oferta
    is_active = models.BooleanField(default=True)  # Indica si la oferta sigue activa

    class Meta:
        unique_together = ("watchdog", "offer_id")
        verbose_name = "Notificación de Watchdog"
        verbose_name_plural = "Notificaciones de Watchdog"

    def __str__(self):
        return f"Notificación para {self.watchdog} - Oferta {self.offer_id}"
