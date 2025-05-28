import logging

import numpy as np
import requests
from allauth.mfa import app_settings
from allauth.mfa.models import Authenticator
from allauth.mfa.utils import is_mfa_enabled
from constance import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from django.views.generic import View
from django.views.generic.edit import CreateView
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from hodlwatcher.users.models import User

from .email_views import send_contact_confirmation_email
from .email_views import send_contact_email
from .forms import ConfiguracionForm
from .forms import ContactForm
from .forms import InvestmentWatchdogForm
from .forms import LinkTelegramForm
from .models import Configuracion
from .models import ContactMessage
from .models import InvestmentWatchdog
from .models import UsuarioTelegram
from .models import WatchdogNotification
from .utils import delete_file
from .utils import extract_currencies
from .utils import extract_payment_methods

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = "app/index.html"


class ContactView(CreateView):
    template_name = "app/contact.html"
    form_class = ContactForm
    model = ContactMessage
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.save()

        send_contact_email()

        send_contact_confirmation_email(form.cleaned_data)

        messages.success(
            self.request, _("Thank you for your message! We'll get back to you soon.")
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("There was an error with your submission. Please try again."),
        )
        return super().form_invalid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Configuracion
    form_class = ConfiguracionForm
    template_name = "app/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        try:
            usuario_telegram = UsuarioTelegram.objects.filter(
                username=self.request.user.username
            ).first()

            configuracion, _ = Configuracion.objects.get_or_create(
                user=self.request.user,
                defaults={
                    "user_telegram": usuario_telegram if usuario_telegram else None
                },
            )
        except UsuarioTelegram.DoesNotExist:
            # Si no se encuentra usuario de Telegram, crea configuración sin él
            configuracion, _ = Configuracion.objects.get_or_create(
                user=self.request.user
            )
            return configuracion
        else:
            return configuracion

    def form_valid(self, form):
        # Guardar referencia a la imagen actual antes de actualizar
        old_instance = self.get_object()
        old_image = None

        if hasattr(old_instance, "image") and old_instance.image:
            old_image = old_instance.image.name

        # Continuar con la lógica original
        form.instance.user = self.request.user

        try:
            usuario_telegram = UsuarioTelegram.objects.filter(
                username=self.request.user.username
            ).first()
            if usuario_telegram:
                form.instance.user_telegram = usuario_telegram
        except UsuarioTelegram.DoesNotExist:
            pass

        # Guardar el formulario con la nueva imagen
        response = super().form_valid(form)

        # Si hay una nueva imagen y existía una imagen antigua, eliminar la antigua
        if old_image and hasattr(form.instance, "image"):
            new_image = form.instance.image.name if form.instance.image else None

            # Solo eliminar si la imagen ha cambiado
            if old_image != new_image and old_image:
                delete_file(old_image)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Intentar obtener configuración de Telegram
        try:
            context["configuracion"] = user.configuracion
        except Configuracion.DoesNotExist:
            context["configuracion"] = None

        authenticators = {}
        for auth in Authenticator.objects.filter(user=self.request.user):
            if auth.type == Authenticator.Type.WEBAUTHN:
                auths = authenticators.setdefault(auth.type, [])
                auths.append(auth.wrap())
            else:
                authenticators[auth.type] = auth.wrap()
        context["authenticators"] = authenticators
        context["MFA_SUPPORTED_TYPES"] = app_settings.SUPPORTED_TYPES
        context["is_mfa_enabled"] = is_mfa_enabled(self.request.user)
        return context


@login_required
@require_POST
def delete_account(request):
    try:
        u = User.objects.get(username=request.user.username)
        u.delete()
        messages.success(request, f"The user {request.user.username} was deleted")

    except User.DoesNotExist:
        messages.error(request, "User doesnot exist")
        return redirect("home")

    except AttributeError as e:
        messages.error(request, _("An unexpected error occurred: ") + str(e))
        return redirect("profile")

    return redirect("account_login")


class BuscadorView(TemplateView):
    template_name = "app/buscador.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_client = self._create_http_client()

    def _create_http_client(self):
        """Crea un cliente HTTP con retries y headers personalizados"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.headers.update(
            {
                "User-Agent": "HodlWatcher/1.0 (+https://hodlwatcher.up.railway.app/)",
                "Accept": "application/json",
            }
        )
        return session

    def get_average_price(self, currency):
        """Obtiene el precio promedio de BTC con cache y manejo de errores"""
        cache_key = f"average_price_{currency}"
        cached_price = cache.get(cache_key)

        if cached_price:
            logger.info("Average price for %s retrieved from cache", currency)
            return cached_price

        exchanges = self._get_exchange_data(currency)
        prices = self._fetch_prices_from_exchanges(exchanges)

        average_price = self._calculate_average_price(prices)
        cache.set(cache_key, average_price, 60 * 11)
        return average_price

    def _get_exchange_data(self, currency):
        """Define exchange data"""
        return [
            (
                "Binance",
                f"https://api.binance.com/api/v3/ticker/price?symbol=BTC{'USDT' if currency == 'USD' else currency}",
                "price",
                1,
            ),
            (
                "Coinbase",
                f"https://api.coinbase.com/v2/prices/BTC-{currency}/spot",
                "data.amount",
                1,
            ),
            (
                "Kraken",
                f"https://api.kraken.com/0/public/Ticker?pair=XBT{currency}",
                "result.XXBTZ{currency}.c.0",
                1,
            ),
            (
                "Gemini",
                f"https://api.gemini.com/v1/pubticker/btc{currency.lower()}",
                "last",
                1,
            ),
        ]

    def _fetch_prices_from_exchanges(self, exchanges):
        """Fetch prices from exchanges"""
        prices = []
        for name, url, price_key, factor in exchanges:
            try:
                price = self._fetch_price_from_exchange(url, price_key)
                if price:
                    price_value = float(price) * factor
                    if price_value > 0:
                        prices.append(price_value)
            except Exception:
                logger.exception("Error en %s", name)
        return prices

    def _fetch_price_from_exchange(self, url, price_key):
        """Fetch price from a single exchange"""
        response = self.http_client.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()

        price = data
        for key in price_key.split("."):
            if key.startswith("[") and key.endswith("]"):
                index = int(key[1:-1])
                price = price[index]
            else:
                price = price.get(key, None)
                if price is None:
                    break
        return price

    def _calculate_average_price(self, prices):
        """Calculate average price with filtering"""
        min_prices_for_average = 2
        if len(prices) >= min_prices_for_average:
            try:
                prices_array = np.array(prices)
                mean = np.mean(prices_array)
                std = np.std(prices_array)
                filtered_prices = [
                    p for p in prices if mean - 2 * std <= p <= mean + 2 * std
                ]
                return (
                    sum(filtered_prices) / len(filtered_prices)
                    if filtered_prices
                    else None
                )
            except ZeroDivisionError:
                return sum(prices) / len(prices) if prices else None
        return None

    def calculate_price_deviation(self, offers, average_price):
        """Calcula la desviación con manejo de errores mejorado"""
        if not offers or not average_price or average_price <= 0:
            return [{"error": _("Invalid input data")}]

        processed_offers = []
        for offer in offers:
            try:
                offer_price = float(offer.get("price", 0))
                percent_deviation = (
                    (offer_price - average_price) / average_price
                ) * 100
                offer["percent_deviation"] = round(percent_deviation, 2)
            except (TypeError, ValueError, KeyError):
                offer["percent_deviation"] = None
                logger.info("Error calculando desviación")
            processed_offers.append(offer)

        return (
            processed_offers
            if processed_offers
            else [{"error": _("No valid offers processed")}]
        )

    def cached_payment_methods(self):
        """Obtiene los métodos de pago con cache"""
        cache_key = "payment_methods"
        cached_payment_methods = cache.get(cache_key)

        if cached_payment_methods:
            logger.info("Payment methods retrieved from cache")
            return cached_payment_methods

        paymet_methods = extract_payment_methods()
        cache.set(cache_key, paymet_methods, 60 * 60 * 24 * 31)  # 31 día
        return paymet_methods

    def cached_currecies(self):
        """Obtiene las monedas de pago con cache"""
        cache_key = "currencies"
        cached_currencies = cache.get(cache_key)

        if cached_currencies:
            logger.info("Currencies retrieved from cache")
            return cached_currencies

        currencies = extract_currencies()
        cache.set(cache_key, currencies, 60 * 60 * 24 * 31)  # 31 día
        return currencies

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request

        # Configuración inicial
        context.update(
            {
                "payment_methods": self.cached_payment_methods(),
                "asset": {"code": "BTC", "name": "Bitcoin"},
                "currencies": self.cached_currecies(),
            }
        )

        params = {
            "side": self.request.GET.get("side", "sell"),
            "asset_code": "BTC",
            "currency_code": self.request.GET.get("currency_code", "EUR"),
            "amount": self.request.GET.get("amount", ""),
        }

        payment_method_id = self.request.GET.get("payment_method_id", "")
        if payment_method_id:
            params["payment_method_id"] = payment_method_id

        context["form_data"] = params
        try:
            # Obtener precio promedio (con cache)
            average_price = self.get_average_price(params["currency_code"])
            context["average_price"] = average_price

            # Obtener ofertas
            response = self.http_client.get(
                "https://hodlhodl.com/api/v1/offers",
                params={
                    **{f"filters[{k}]": v for k, v in params.items()},
                    "filters[include_global]": "true",
                    "pagination[limit]": "100",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Filtrar y procesar ofertas
            no_trades = self.request.GET.get("new_user")
            if no_trades:
                offers = [
                    offer
                    for offer in data.get("offers", [])
                    if offer.get("trader", {}).get("trades_count", 0) >= 0
                ]
            else:
                offers = [
                    offer
                    for offer in data.get("offers", [])
                    if offer.get("trader", {}).get("trades_count", 0) >= 1
                ]
            context["no_trades"] = no_trades
            offers = self.calculate_price_deviation(offers, average_price)
            if params["side"] == "buy":
                context["offers"] = sorted(
                    offers, key=lambda x: x["percent_deviation"], reverse=True
                )
            else:
                context["offers"] = offers
            context["meta"] = data.get("meta", {})

        except requests.RequestException as e:
            context["error"] = f"Error al obtener datos: {e!s}"
            context["offers"] = []
            context["average_price"] = None

        return context


class WatchdogListView(LoginRequiredMixin, ListView):
    model = InvestmentWatchdog
    template_name = "app/watchdog_list.html"
    context_object_name = "watchdogs"

    def get_queryset(self):
        return self.request.user.watchdogs.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir watchdogs inactivos
        context["inactive_watchdogs"] = self.request.user.watchdogs.filter(active=False)
        # Añadir contador y límite
        context["current_count"] = self.get_queryset().count()
        context["max_watchdogs"] = config.MAX_WATCHDOGS
        context["historial_alertas"] = WatchdogNotification.objects.filter(
            watchdog__user=self.request.user
        ).prefetch_related("watchdog")

        payment_methods = cache.get("payment_methods") or []

        # Crear un diccionario para búsqueda rápida por ID
        payment_methods_dict = {
            method["id"]: method["name"] for method in payment_methods
        }
        context["payment_methods_dict"] = payment_methods_dict

        return context


class WatchdogCreateView(LoginRequiredMixin, CreateView):
    model = InvestmentWatchdog
    form_class = InvestmentWatchdogForm
    template_name = "app/watchdog_form.html"
    success_url = reverse_lazy("watchdogs_list")

    def get_form_kwargs(self):
        """Añadir el usuario_telegram a los kwargs del formulario."""
        kwargs = super().get_form_kwargs()

        # Buscar el usuario_telegram asociado al usuario actual
        try:
            configuracion = Configuracion.objects.get(user=self.request.user)
            kwargs["usuario_telegram"] = configuracion.user_telegram
        except Configuracion.DoesNotExist:
            # Si no existe configuración, intentar buscar directamente el usuario_telegram
            try:
                usuario_telegram = UsuarioTelegram.objects.filter(
                    username=self.request.user.username
                ).first()
                kwargs["usuario_telegram"] = usuario_telegram
            except UsuarioTelegram.DoesNotExist:
                pass

        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            {
                "side": self.request.GET.get("side", "sell"),
                "payment_method_id": self.request.GET.get("payment_method_id", "EUR"),
                "asset_code": "BTC",
                "currency": self.request.GET.get("currency_code", "EUR"),
                "amount": self.request.GET.get("amount", "150"),
                "rate_fee": self.request.GET.get("rate_fee", "0"),
            }
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "payment_methods": [
                    {"code": "EUR", "name": "Transferencia SEPA"},
                    {"code": "USD", "name": "Transferencia Bancaria"},
                ],
                "assets": {"code": "BTC", "name": "Bitcoin"},
                "currencies": [
                    {"code": "EUR", "name": "Euros"},
                    {"code": "USD", "name": "Dólar Americano"},
                ],
                "current_count": self.request.user.watchdogs.filter(
                    active=True
                ).count(),
                "max_watchdogs": config.MAX_WATCHDOGS,
            }
        )

        # Preparar datos para el resumen
        form = context["form"]
        summary_data = {
            "side": dict(InvestmentWatchdog.SIDE_CHOICES).get(
                form["side"].value(), "sell"
            ),
            "currency": next(
                (
                    c["name"]
                    for c in context["currencies"]
                    if c["code"] == form["currency"].value()
                ),
                "EUR",
            ),
            "payment_method": next(
                (
                    p["name"]
                    for p in context["payment_methods"]
                    if p["code"] == form["payment_method_id"].value()
                ),
                "Transferencia SEPA",
            ),
            "asset": "Bitcoin",
            "amount": form["amount"].value() or "150",
            "rate_fee": f"{float(form['rate_fee'].value() or 0):.2f}%",
        }
        context["summary_data"] = summary_data

        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Watchdog successfully created"))
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        try:
            if (
                request.user.watchdogs.filter(active=True).count()
                >= config.MAX_WATCHDOGS
            ):
                messages.error(
                    request,
                    _(
                        "You already have the maximum of {} active watchdogs. Please deactivate one before creating another."
                    ).format(config.MAX_WATCHDOGS),
                )
                return redirect("watchdogs_list")
        except AttributeError:
            pass
        return super().dispatch(request, *args, **kwargs)


class WatchdogActivateView(LoginRequiredMixin, View):
    """
    Vista para activar un watchdog desactivado
    """

    def post(self, request, pk):
        try:
            watchdog = get_object_or_404(InvestmentWatchdog, pk=pk, user=request.user)

            # Verificar límite de watchdogs activos
            max_watchdogs = config.MAX_WATCHDOGS
            active_count = request.user.watchdogs.filter(active=True).count()

            if active_count >= max_watchdogs:
                messages.error(
                    request,
                    _("You have reached the limit of active watchdogs for your plan."),
                )
            else:
                watchdog.active = True
                watchdog.save()
                messages.success(request, _("Watchdog activated correctly."))

        except InvestmentWatchdog.DoesNotExist:
            messages.error(
                request,
                _(
                    "The watchdog does not exist or you do not have permission to activate it."
                ),
            )

        return redirect("watchdogs_list")


class WatchdogDeactivateView(LoginRequiredMixin, View):
    """
    Vista para desactivar un watchdog activo
    """

    def post(self, request, pk):
        try:
            watchdog = get_object_or_404(InvestmentWatchdog, pk=pk, user=request.user)
            watchdog.active = False
            watchdog.save()
            messages.info(request, _("Watchdog deactivated correctly."))

        except InvestmentWatchdog.DoesNotExist:
            messages.error(
                request,
                _(
                    "The watchdog does not exist or you do not have permission to disable it."
                ),
            )

        return redirect("watchdogs_list")


class DeleteWatchdogView(LoginRequiredMixin, DeleteView):
    """
    Vista para eliminar definitivamente un watchdog
    """

    model = InvestmentWatchdog
    success_url = reverse_lazy("watchdogs_list")

    def get_queryset(self):
        # Solo permitir eliminar watchdogs del usuario autenticado que estén desactivados
        return InvestmentWatchdog.objects.filter(user=self.request.user, active=False)

    def form_valid(self, form):
        messages.warning(self.request, _("Watchdog removed permanently."))
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        # Redirigir a la lista de watchdogs si se intenta acceder directamente a la URL
        messages.warning(
            self.request, _("Please use the delete button from the watchdogs list.")
        )
        return redirect("watchdogs_list")


# Vista para vincular cuenta de Telegram
class LinkTelegramView(LoginRequiredMixin, FormView):
    template_name = "app/link_telegram.html"
    form_class = LinkTelegramForm
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        username = form.cleaned_data["username"]

        try:
            # Buscar el usuario de Telegram por username
            user_telegram = UsuarioTelegram.objects.get(username=username)

            # Verificar si ya está vinculado a otro usuario
            existing_config = Configuracion.objects.filter(
                user_telegram=user_telegram
            ).first()
            if existing_config and existing_config.user != self.request.user:
                messages.error(
                    self.request,
                    _("This Telegram user is already linked to another account."),
                )
                return redirect("link_telegram")

            # Actualizar la configuración del usuario
            config, created = Configuracion.objects.get_or_create(
                user=self.request.user
            )
            config.user_telegram = user_telegram
            config.save()

            messages.success(self.request, _("Telegram account successfully linked!"))

        except UsuarioTelegram.DoesNotExist:
            messages.error(
                self.request,
                _(
                    "No Telegram user with that name was found. Please make sure you have started our bot with /start."
                ),
            )
            return redirect("link_telegram")

        return super().form_valid(form)


class UnlinkTelegramView(LoginRequiredMixin, View):
    """Vista para desvincular la cuenta de Telegram."""

    def post(self, request, *args, **kwargs):
        try:
            configuracion = request.user.configuracion
            if configuracion.user_telegram:
                # Solo desvinculamos, no eliminamos el usuario de Telegram
                configuracion.user_telegram = None
                configuracion.save()
                messages.success(
                    request, _("Your Telegram account has been successfully unlinked.")
                )
            else:
                messages.info(
                    request, _("You didn't have any linked Telegram accounts.")
                )
        except Configuracion.DoesNotExist:
            messages.error(request, _("Your configuration was not found."))

        return redirect("profile")
