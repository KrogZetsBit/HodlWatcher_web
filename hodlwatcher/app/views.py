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
from .utils import get_or_create_user_config_with_telegram

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

        messages.success(self.request, _("Thank you for your message! We'll get back to you soon."))
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
        return get_or_create_user_config_with_telegram(self.request.user)

    def _delete_old_image_if_changed(self, old_image_name, new_image_instance):
        """
        Deletes the old image if it has changed and exists.
        """
        if not old_image_name or not new_image_instance:
            return

        new_image_name = new_image_instance.name if new_image_instance else None

        if old_image_name != new_image_name:
            delete_file(old_image_name)

    def form_valid(self, form):
        old_instance = self.get_object()
        old_image_name = old_instance.image.name if hasattr(old_instance, "image") and old_instance.image else None

        form.instance.user = self.request.user
        # Ensure user_telegram is correctly associated, get_or_create_user_config_with_telegram handles this in get_object
        # but if the form directly manipulates user_telegram, it might need re-association.
        # However, the form ConfiguracionForm does not seem to directly expose user_telegram for editing.
        # So, relying on get_object's handling should be sufficient.

        response = super().form_valid(form)

        # Delete old image if a new one was uploaded
        self._delete_old_image_if_changed(old_image_name, form.instance.image)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["configuracion"] = self.get_object()  # Use get_object to ensure consistency

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

    # Catching a broad AttributeError here. This might occur if `request.user` for some reason
    # does not have a `username` attribute or if `u` is None before delete, though Django's
    # get_object_or_404 or direct .get() would typically raise User.DoesNotExist first.
    # It could also be other unexpected attribute errors within the try block.
    except AttributeError as e:
        logger.error("AttributeError during account deletion for user %s: %s", request.user.username, e)
        messages.error(request, _("An unexpected error occurred: ") + str(e))
        return redirect("profile")

    return redirect("account_login")


class BuscadorView(TemplateView):
    template_name = "app/buscador.html"
    EXCHANGE_CONFIGS = [
        {
            "name": "Binance",
            "url_template": "https://api.binance.com/api/v3/ticker/price?symbol=BTC{}",
            "currency_param_processor": lambda currency: "USDT" if currency == "USD" else currency,
            "price_key": "price",
            "factor": 1,
        },
        {
            "name": "Coinbase",
            "url_template": "https://api.coinbase.com/v2/prices/BTC-{}/spot",
            "currency_param_processor": lambda currency: currency,
            "price_key": "data.amount",
            "factor": 1,
        },
        {
            "name": "Kraken",
            "url_template": "https://api.kraken.com/0/public/Ticker?pair=XBT{}",
            "currency_param_processor": lambda currency: currency,
            "price_key": "result.XXBTZ{}.c.0",  # Note: currency needs to be injected here too
            "factor": 1,
        },
        {
            "name": "Gemini",
            "url_template": "https://api.gemini.com/v1/pubticker/btc{}",
            "currency_param_processor": lambda currency: currency.lower(),
            "price_key": "last",
            "factor": 1,
        },
    ]

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

    def _get_exchange_data(self, currency):
        """Generates exchange data based on the currency from EXCHANGE_CONFIGS."""
        exchange_data = []
        for config_item in self.EXCHANGE_CONFIGS:
            processed_currency = config_item["currency_param_processor"](currency)
            url = config_item["url_template"].format(processed_currency)
            # Special handling for Kraken's price_key which also needs currency
            price_key = config_item["price_key"]
            if config_item["name"] == "Kraken":
                price_key = config_item["price_key"].format(currency)

            exchange_data.append(
                (
                    config_item["name"],
                    url,
                    price_key,
                    config_item["factor"],
                )
            )
        return exchange_data

    def _fetch_prices_from_exchanges(self, exchanges):
        """Fetch prices from exchanges"""
        prices = []
        for name, url, price_key, factor in exchanges:
            try:
                price = self._fetch_price_from_exchange(name, url, price_key)
                if price:
                    price_value = float(price) * factor
                    if price_value > 0:
                        prices.append(price_value)
            except requests.RequestException as e:
                logger.error("Error fetching price from %s: %s", name, e)
            except (ValueError, KeyError) as e:
                logger.error("Error parsing price from %s: %s", name, e)
            except Exception as e: # Catch any other unexpected errors
                logger.exception("Unexpected error processing exchange %s: %s", name, e)
        return prices

    def _fetch_price_from_exchange(self, exchange_name, url, price_key):
        """Fetch price from a single exchange"""
        try:
            response = self.http_client.get(url, timeout=3)
            response.raise_for_status()
            data = response.json()

            price = data
            for key_part in price_key.split("."):
                if key_part.startswith("[") and key_part.endswith("]"):
                    try:
                        index = int(key_part[1:-1])
                        price = price[index]
                    except (IndexError, ValueError) as e:
                        logger.error("Error accessing index %s in price data for %s. Data: %s", key_part, exchange_name, price)
                        raise KeyError(f"Invalid index {key_part} for {exchange_name}") from e
                else:
                    price = price.get(key_part, None)
                    if price is None:
                        logger.warning("Price key '%s' not found for %s in data. URL: %s", price_key, exchange_name, url)
                        return None # Or raise KeyError if this should be fatal
            return price
        except requests.RequestException as e:
            logger.error("HTTP error fetching price for %s from %s: %s", exchange_name, url, e)
            raise  # Re-raise to be caught by the caller
        except ValueError as e: # JSONDecodeError inherits from ValueError
            logger.error("JSON decoding error for %s from %s: %s", exchange_name, url, e)
            raise # Re-raise to be caught by the caller


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
        cache.set(cache_key, average_price, 60 * 11) # Cache for 11 minutes
        return average_price

    def _calculate_average_price(self, prices):
        """Calculate average price with filtering. Original logic preserved."""
        min_prices_for_average = 2
        if len(prices) >= min_prices_for_average:
            try:
                prices_array = np.array(prices)
                mean = np.mean(prices_array)
                std = np.std(prices_array)
                filtered_prices = [p for p in prices if mean - 2 * std <= p <= mean + 2 * std]
                return sum(filtered_prices) / len(filtered_prices) if filtered_prices else None
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
                percent_deviation = ((offer_price - average_price) / average_price) * 100
                offer["percent_deviation"] = round(percent_deviation, 2)
            except (TypeError, ValueError, KeyError):
                offer["percent_deviation"] = None
                logger.info("Error calculando desviación")
            processed_offers.append(offer)

        return processed_offers if processed_offers else [{"error": _("No valid offers processed")}]

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
        context["request"] = self.request # For template access to request object

        # Initial data for the form and context
        context.update({
            "payment_methods": self.cached_payment_methods(),
            "asset": {"code": "BTC", "name": "Bitcoin"}, # Currently fixed
            "currencies": self.cached_currecies(),
        })

        params = self._get_request_params()
        context["form_data"] = params

        try:
            average_price = self.get_average_price(params["currency_code"])
            context["average_price"] = average_price

            offers_data = self._fetch_hodlhodl_offers(params)
            processed_offers, meta = self._process_offers(
                offers_data,
                average_price,
                params["side"],
                self.request.GET.get("new_user") # no_trades filter
            )
            context["offers"] = processed_offers
            context["meta"] = meta
            context["no_trades"] = self.request.GET.get("new_user")

        except requests.RequestException as e:
            logger.error("Error fetching data for BuscadorView: %s", e)
            context["error"] = f"Error al obtener datos: {e!s}"
            context["offers"] = []
            context["average_price"] = None
        except Exception as e: # Catch any other unexpected errors
            logger.exception("Unexpected error in BuscadorView.get_context_data: %s", e)
            context["error"] = _("An unexpected error occurred.")
            context["offers"] = []
            context["average_price"] = None
        return context

    def _get_request_params(self):
        """Extracts and manages request GET parameters."""
        return {
            "side": self.request.GET.get("side", "sell"),
            "payment_method_id": self.request.GET.get("payment_method_id", "52"), # Default SEPA
            "asset_code": "BTC", # Fixed for now
            "currency_code": self.request.GET.get("currency_code", "EUR"),
            "amount": self.request.GET.get("amount", ""),
        }

    def _fetch_hodlhodl_offers(self, params):
        """Handles the API call to HodlHodl."""
        api_params = {
            **{f"filters[{k}]": v for k, v in params.items() if v}, # Ensure only params with values are sent
            "filters[include_global]": "true",
            "pagination[limit]": "100", # Consider making this configurable or dynamic
        }
        response = self.http_client.get("https://hodlhodl.com/api/v1/offers", params=api_params)
        response.raise_for_status() # Will raise HTTPError for bad responses (4XX or 5XX)
        return response.json()

    def _process_offers(self, offers_data, average_price, side, no_trades_filter):
        """Filters and processes offers."""
        offers_list = offers_data.get("offers", [])

        if no_trades_filter: # 'new_user' effectively means trades_count >= 0
            filtered_by_trades = [
                offer for offer in offers_list if offer.get("trader", {}).get("trades_count", 0) >= 0
            ]
        else: # Default is trades_count >= 1
            filtered_by_trades = [
                offer for offer in offers_list if offer.get("trader", {}).get("trades_count", 0) >= 1
            ]

        processed_offers = self.calculate_price_deviation(filtered_by_trades, average_price)

        if side == "buy":
            # For buy offers, sort by percent_deviation descending (best deals first)
            # Ensure 'percent_deviation' exists and handle None if necessary
            processed_offers.sort(key=lambda x: x.get("percent_deviation", -float('inf')) if x.get("percent_deviation") is not None else -float('inf'), reverse=True)
        # For sell offers, default sorting (as returned by API or by price deviation calculation) is usually fine.
        # If specific sorting is needed for sell, it would be added here.

        return processed_offers, offers_data.get("meta", {})


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
        ).select_related("watchdog") # Use select_related for ForeignKey

        # Get payment_methods from cache (assuming it's populated by BuscadorView or similar)
        # The structure from extract_payment_methods is a list of dicts: [{'id': 'X', 'name': 'Y', ...}]
        payment_methods_list = cache.get("payment_methods") or extract_payment_methods() # Ensure it's loaded if not in cache

        # Crear un diccionario para búsqueda rápida por ID
        # This is efficient enough for typical numbers of payment methods.
        payment_methods_dict = {str(method["id"]): method["name"] for method in payment_methods_list}
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
        configuracion = get_or_create_user_config_with_telegram(self.request.user)
        kwargs["usuario_telegram"] = configuracion.user_telegram
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

        # Fetch dynamic data for dropdowns, similar to BuscadorView
        # Ensure these utils return data in a format suitable for the template/form
        # extract_payment_methods returns list of dicts with 'id', 'name', 'type'
        # extract_currencies returns list of dicts with 'code', 'name'
        cached_payment_methods = cache.get("payment_methods") or extract_payment_methods()
        cached_currencies = cache.get("currencies") or extract_currencies()

        context.update({
            "payment_methods": cached_payment_methods,
            "assets": [{"code": "BTC", "name": "Bitcoin"}], # Currently fixed asset
            "currencies": cached_currencies,
            "current_count": self.request.user.watchdogs.filter(active=True).count(),
            "max_watchdogs": config.MAX_WATCHDOGS,
        })

        # Preparar datos para el resumen
        form = context.get("form") # Get the form instance from context
        if form: # Ensure form is present
            summary_data = {
                "side": dict(InvestmentWatchdog.SIDE_CHOICES).get(form.initial.get("side") or form.data.get("side", "sell")),
                "currency": next(
                    (c["name"] for c in cached_currencies if c["code"] == (form.initial.get("currency") or form.data.get("currency"))),
                    "N/A",
                ),
                "payment_method": next(
                    (pm["name"] for pm in cached_payment_methods if str(pm["id"]) == str(form.initial.get("payment_method_id") or form.data.get("payment_method_id"))),
                    "N/A",
                ),
                "asset": "Bitcoin", # Fixed
                "amount": form.initial.get("amount") or form.data.get("amount", "0"),
                "rate_fee": f"{float(form.initial.get('rate_fee') or form.data.get('rate_fee', 0)):.2f}%",
            }
            context["summary_data"] = summary_data
        else:
            context["summary_data"] = {}


        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Watchdog successfully created"))
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.watchdogs.filter(active=True).count() >= config.MAX_WATCHDOGS:
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
                _("The watchdog does not exist or you do not have permission to activate it."),
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
                _("The watchdog does not exist or you do not have permission to disable it."),
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
        messages.warning(self.request, _("Please use the delete button from the watchdogs list."))
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
            existing_config = Configuracion.objects.filter(user_telegram=user_telegram).first()
            if existing_config and existing_config.user != self.request.user:
                messages.error(
                    self.request,
                    _("This Telegram user is already linked to another account."),
                )
                return redirect("link_telegram")

            # Actualizar la configuración del usuario
            # Use the utility function to ensure Configuracion exists and link Telegram user
            configuracion = get_or_create_user_config_with_telegram(self.request.user)
            configuracion.user_telegram = user_telegram # Link the found UserTelegram
            configuracion.save()

            messages.success(self.request, _("Telegram account successfully linked!"))

        except UsuarioTelegram.DoesNotExist:
            messages.error(
                self.request,
                _("No Telegram user with that name was found. Please make sure you have started our bot with /start."),
            )
            return redirect("link_telegram")
        except Exception as e: # Catch other potential errors
            logger.error("Error linking Telegram account for user %s: %s", self.request.user.username, e)
            messages.error(self.request, _("An unexpected error occurred while linking the Telegram account."))
            return redirect("link_telegram")


        return super().form_valid(form)


class UnlinkTelegramView(LoginRequiredMixin, View):
    """Vista para desvincular la cuenta de Telegram."""

    def post(self, request, *args, **kwargs):
        try:
            # Use the utility function to get configuration, ensuring it exists
            configuracion = get_or_create_user_config_with_telegram(request.user)
            if configuracion.user_telegram:
                configuracion.user_telegram = None
                configuracion.save()
                messages.success(request, _("Your Telegram account has been successfully unlinked."))
            else:
                messages.info(request, _("You didn't have any linked Telegram accounts."))
        # Configuracion.DoesNotExist should not happen if get_or_create_user_config_with_telegram is used,
        # but kept for safety or if called from elsewhere without this utility.
        except Configuracion.DoesNotExist: # Should be rare with get_or_create_user_config_with_telegram
            logger.warning("Configuracion.DoesNotExist during unlink for user %s", request.user.username)
            messages.error(request, _("Your configuration was not found."))
        except Exception as e:
            logger.error("Error unlinking Telegram account for user %s: %s", request.user.username, e)
            messages.error(self.request, _("An unexpected error occurred while unlinking the Telegram account."))


        return redirect("profile")
