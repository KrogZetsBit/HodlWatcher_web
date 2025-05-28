import json
import logging
import time
from decimal import Decimal

import requests
from constance import config
from django.core.cache import cache
from django.core.files.storage import default_storage
from telegram.error import TelegramError
from telegram.ext import Application

from .email_views import send_watchdog_notification
from .models import WatchdogNotification

logger = logging.getLogger(__name__)


def obtener_ofertas(token, url_base, parametros):
    """
    Obtiene ofertas de la API con los parámetros especificados.

    Args:
        token (str): El token de autenticación Bearer.
        url_base (str): La URL base de la API.
        parametros (dict): Un diccionario con los parámetros de la petición.

    Returns:
        dict: La respuesta de la API en formato JSON, o None si ocurre un error.
    """
    url = f"{url_base}/api/v1/offers"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        respuesta = requests.get(url, headers=headers, params=parametros, timeout=6)
        respuesta.raise_for_status()  # Lanza una excepción para códigos de estado HTTP erróneos
        return respuesta.json()

    except requests.exceptions.RequestException:
        logger.info("Error al hacer la petición a la API")
        return None
    except json.JSONDecodeError:
        logger.info("Error al decodificar la respuesta JSON")
        return None


def extract_payment_methods():
    """
    Extrae los métodos de pago de un JSON, devolviendo solo el id, type y name.
    Opcionalmente los ordena por ID.

    Args:
        json_data (dict or str): Datos JSON con la estructura de métodos de pago.
        sort_by_id (bool, optional): Si se deben ordenar los métodos por ID. Por defecto es True.

    Returns:
        list: Lista de métodos de pago con id, type y name.
    """

    json_data = requests.get("https://hodlhodl.com/api/v1/payment_methods", timeout=6).json()
    # Si se pasa un string, convertir a diccionario
    if isinstance(json_data, str):
        json_data = json.loads(json_data)

    # Extraer los métodos de pago
    extracted_methods = [
        {
            "id": method.get("id", ""),
            "type": method.get("type", ""),
            "name": method.get("name", ""),
        }
        for method in json_data.get("payment_methods", [])
    ]

    # Añadir opción "Todos los métodos" o similar
    empty_method = {
        "id": "",
        "type": "",
        "name": "-- Seleccionar método --",  # o "Todos los métodos"
    }

    return [empty_method, *sorted(extracted_methods, key=lambda x: x["name"])]


def extract_currencies():
    """
    Extrae las monedas de pago de un JSON, devolviendo solo el id, type y name.
    Opcionalmente los ordena por ID.

    Args:
        json_data (dict or str): Datos JSON con la estructura de monedas.
        sort_by_id (bool, optional): Si se deben ordenar los métodos por ID. Por defecto es True.

    Returns:
        list: Lista de monedas con id, type y name.
    """

    json_data = requests.get("https://hodlhodl.com/api/v1/currencies", timeout=6).json()
    # Si se pasa un string, convertir a diccionario
    if isinstance(json_data, str):
        json_data = json.loads(json_data)

    # Extraer las monedas
    extracted_currencies = [
        {"code": method.get("code", ""), "name": method.get("name", "")} for method in json_data.get("currencies", [])
    ]

    return sorted(extracted_currencies, key=lambda x: x["name"])


def get_matching_offers(watchdog):
    """
    Obtiene ofertas que coinciden con los criterios del watchdog desde la API,
    teniendo en cuenta la tasa de comisión y el precio actual del asset.

    Args:
        watchdog (InvestmentWatchdog): El watchdog a comprobar

    Returns:
        list: Lista de ofertas coincidentes
    """
    # Configurar parámetros para la solicitud a la API
    params = {
        "filters[side]": watchdog.side,
        "filters[payment_method_id]": watchdog.payment_method_id,
        "filters[asset_code]": watchdog.asset_code,
        "filters[currency_code]": watchdog.currency,
        "filters[amount]": str(watchdog.amount),
        "filters[include_global]": "true",
        "pagination[limit]": "100",
    }

    # Realizar solicitud a la API
    try:
        response = requests.get("https://hodlhodl.com/api/v1/offers", params=params, timeout=6)
        response.raise_for_status()
        data = response.json()
        # Filtrar ofertas por número de operaciones del trader (al menos 1)
        offers = [offer for offer in data.get("offers", []) if offer.get("trader", {}).get("trades_count", 0) >= 1]

        # Aplicar el filtro de rate_fee
        fee_threshold = 100  # Define a constant for the magic value

        filtered_offers = []
        filtered_fees = []
        for offer in offers:
            # Obtener el precio actual del asset desde la caché
            cache_key = f"average_price_{watchdog.currency}"
            cached_price = cache.get(cache_key)

            if cached_price is not None:
                offer_price = Decimal(offer.get("price", "0"))
                # Calcular el fee de la oferta en base al precio actual
                real_price = Decimal(cached_price)

                # Calcular el fee máximo permitido para este watchdog
                real_fee = offer_price / real_price * fee_threshold
                fee = float(real_fee - fee_threshold) if real_fee > fee_threshold else float(fee_threshold - real_fee)
                # Verificar si el fee de la oferta es menor o igual al máximo permitido
                if fee <= watchdog.rate_fee:
                    filtered_offers.append(offer)
                    filtered_fees.append(fee)
            else:
                logger.warning(
                    "Precio en caché no encontrado para %s. No se puede aplicar el filtro de fee.",
                    watchdog.currency,
                )

    except requests.RequestException:
        logger.exception("Error al obtener ofertas desde la API")
        return []

    else:
        return {
            "Filtered_offers": filtered_offers,
            "Filtered_fees": filtered_fees,
        }


def process_watchdog(watchdog):
    """
    Procesa un watchdog individual, buscando ofertas coincidentes y enviando notificaciones.
    """
    try:
        matching_offers = get_matching_offers(watchdog)

        if matching_offers:
            new_offers = filter_new_offers(watchdog, matching_offers["Filtered_offers"])
            if new_offers:
                send_watchdog_notification(watchdog, new_offers, matching_offers["Filtered_fees"])
                logger.info(
                    logger.info(
                        "Notificación enviada para watchdog %s. Se encontraron %s nuevas ofertas",
                        watchdog.id,
                        len(new_offers),
                    )
                )
            else:
                logger.debug("No hay nuevas ofertas para notificar en watchdog %s", watchdog.id)
        else:
            logger.debug("No se encontraron ofertas para watchdog %s", watchdog.id)

    except Exception:
        logger.exception("Error al procesar watchdog %s", watchdog.id)
    time.sleep(2)


def filter_new_offers(watchdog, offers):
    """
    Filtra las ofertas que no han sido notificadas previamente.
    """
    new_offers = []
    for offer in offers:
        offer_id = offer.get("id")
        if offer_id and not WatchdogNotification.objects.filter(watchdog=watchdog, offer_id=offer_id).exists():
            new_offers.append(offer)
            WatchdogNotification.objects.create(watchdog=watchdog, offer_id=offer_id)
    return new_offers


async def enviar_alerta_watchdog(investment_watchdog, mensaje):
    """
    Envía una alerta a los usuarios de Telegram cuando se activa un InvestmentWatchdog.

    Args:
        investment_watchdog: La instancia del InvestmentWatchdog que generó la alerta
        mensaje: El mensaje de alerta a enviar
    """
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no está configurado")
        return

    try:
        # Obtener el usuario relacionado con este watchdog
        usuario = investment_watchdog.usuario

        # Buscar la configuración del usuario
        if hasattr(usuario, "configuracion") and usuario.configuracion.user_telegram:
            user_telegram = usuario.configuracion.user_telegram

            # Verificar si tiene activadas las alertas
            if user_telegram.recibir_alertas_watchdog and investment_watchdog.activo:
                # Inicializar la aplicación de telegram
                app = Application.builder().token(token).build()

                # Construir el mensaje de alerta
                condicion = "por encima de" if investment_watchdog.condicion == "above" else "por debajo de"
                alert_message = (
                    f"🚨 *ALERTA DE WATCHDOG* 🚨\n\n"
                    f"*{investment_watchdog.nombre}*\n"
                    f"{mensaje}\n\n"
                    f"Cripto: {investment_watchdog.cripto.symbol}\n"
                    f"Condición: {condicion} ${float(investment_watchdog.precio_objetivo):.2f}\n"
                    f"Precio actual: ${float(investment_watchdog.last_price):.2f}"
                )

                # Enviar el mensaje
                async with app:
                    await app.bot.send_message(
                        chat_id=user_telegram.chat_id,
                        text=alert_message,
                        parse_mode="Markdown",
                    )
                logger.info("Alerta de watchdog enviada a %s", user_telegram.username)
            else:
                logger.info(
                    "Usuario %s tiene desactivadas las alertas de watchdog o el watchdog está inactivo",
                    usuario.username,
                )
        else:
            logger.info("Usuario %s no tiene configurado Telegram", usuario.username)

    except TelegramError:
        logger.exception("Error de Telegram al enviar alerta")
    except Exception:
        logger.exception("Error al enviar alerta de watchdog")


# Función para enviar una alerta de prueba (útil para verificar la configuración)
async def enviar_alerta_prueba(chat_id):
    """Envía una alerta de prueba al chat especificado."""
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN no está configurado")
        return False

    try:
        # Inicializar la aplicación de telegram
        app = Application.builder().token(token).build()

        # Mensaje de prueba
        test_message = (
            "🧪 *ALERTA DE PRUEBA* 🧪\n\n"
            "Esta es una alerta de prueba para verificar que las notificaciones "
            "de tu HodlWatcher están funcionando correctamente.\n\n"
            "Si recibes este mensaje, tu configuración es correcta."
        )

        # Enviar el mensaje
        async with app:
            await app.bot.send_message(chat_id=chat_id, text=test_message, parse_mode="Markdown")

    except Exception:
        logger.exception("Error al enviar alerta de prueba")
        return False

    return True


def delete_file(file_path):
    """
    Elimina un archivo del almacenamiento actual (S3 o MinIO)
    independientemente del entorno.

    Args:
        file_path (str): Ruta relativa al archivo a eliminar

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("Imagen antigua eliminada %s", file_path)
            return True
    except Exception:
        logger.exception("Error al eliminar archivo %s", file_path)
        return False
    else:
        return False
