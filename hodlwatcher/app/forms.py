from constance import config
from django import forms
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from .models import Configuracion
from .models import ContactMessage
from .models import InvestmentWatchdog


class ContactForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3)
    privacy_policy = forms.BooleanField(label="I have read and agree to the Privacy Policy", required=True)

    class Meta:
        model = ContactMessage
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "message",
            "captcha",
            "privacy_policy",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }
        labels = {
            "name": "Your Name",
            "email": "Your Email Address",
            "phone": "Your Phone Number (optional)",
            "subject": "Subject",
            "message": "Your Message",
        }


class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = ["image"]
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }


class InvestmentWatchdogForm(forms.ModelForm):
    # Definir los campos explícitamente para poder asignarles choices
    currency = forms.ChoiceField(label="Currency", widget=forms.Select(attrs={"class": "form-select select2"}))

    payment_method_id = forms.ChoiceField(
        label="Method of payment",
        widget=forms.Select(attrs={"class": "form-select select2"}),
    )

    asset_code = forms.CharField(
        label="Asset",
        initial="Bitcoin (BTC)",  # Valor por defecto
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        # Extraer el usuario_telegram del kwargs (si existe)
        self.usuario_telegram = kwargs.pop("usuario_telegram", None)

        super().__init__(*args, **kwargs)

        # Get payment_methods and currencies from cache
        cache_key_payment_methods = "payment_methods"
        cached_payment_methods = cache.get(cache_key_payment_methods) or []

        cache_key_currencies = "currencies"
        cached_currencies = cache.get(cache_key_currencies) or []

        # Create options for payment_method_id
        payment_method_choices = [
            (method["id"], f"{method['name']} ({method['type']})") for method in cached_payment_methods
        ]
        self.fields["payment_method_id"].choices = payment_method_choices

        # Create options for currencies
        currency_choices = [(method["code"], f"{method['name']}") for method in cached_currencies]

        self.fields["currency"].choices = currency_choices

    class Meta:
        model = InvestmentWatchdog
        fields = [
            "side",
            "asset_code",
            "payment_method_id",
            "amount",
            "currency",
            "rate_fee",
        ]
        widgets = {
            "side": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Introduce la cantidad"}),
            "rate_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
        }
        labels = {
            "side": "Type of operation",
            "amount": "Quantity",
            "rate_fee": "Fee rate (%)",
        }

    def clean(self):
        cleaned_data = super().clean()
        user = self.instance.user if hasattr(self.instance, "user") else None

        if user and user.watchdogs.filter(active=True).count() >= config.MAX_WATCHDOGS:
            raise ValidationError(
                _(
                    "You already have the maximum of %s active watchdogs. Please deactivate one before creating another.",
                    config.MAX_WATCHDOGS,
                )
            )

        return cleaned_data

    def save(self, commit=True):  # noqa: FBT002
        instance = super().save(commit=False)

        # Asignar el usuario_telegram si está disponible
        if self.usuario_telegram:
            instance.usuario_telegram = self.usuario_telegram

        if commit:
            instance.save()

        return instance


# Formulario para vincular cuenta de Telegram
class LinkTelegramForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Enter your Telegram user name without the initial @",
    )
