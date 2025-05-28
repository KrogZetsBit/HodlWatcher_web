import logging

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from . import utils
from .models import InvestmentWatchdog, WatchdogNotification
from .views import BuscadorView

logger_task = get_task_logger(__name__)
logger = logging.getLogger(__name__)


@shared_task()
def celery_hello(message="Hello Celery!"):
    logger_task.info(message)
    return {"message": message}


@shared_task
def update_price_cache():
    currencies = ["EUR", "USD"]  # Divisas soportadas
    view = BuscadorView()
    for currency in currencies:
        view.get_average_price(currency)


@shared_task
def update_payment_methods():
    view = BuscadorView()
    view.cached_payment_methods()


@shared_task
def update_currencies():
    view = BuscadorView()
    view.cached_currecies()


@shared_task
def check_watchdogs():
    """
    Tarea que comprueba todos los InvestmentWatchdog activos y envía
    notificaciones por correo si se encuentran ofertas coincidentes.
    """
    watchdogs = InvestmentWatchdog.objects.filter(active=True)

    if not watchdogs:
        logger_task.info("No hay watchdogs activos para comprobar")
        return

    logger_task.info("Comprobando %s watchdogs activos", watchdogs.count())

    for watchdog in watchdogs:
        utils.process_watchdog(watchdog)


@shared_task
def clean_old_notifications():
    """
    Elimina notificaciones antiguas (más de 7 días)
    """
    # Calcular la fecha de hace 7 días
    cutoff_date = timezone.now() - timezone.timedelta(days=7)

    # Eliminar notificaciones anteriores a esa fecha
    deleted_count, _ = WatchdogNotification.objects.filter(notified_at__lt=cutoff_date).delete()

    logger.info("Se eliminaron %s notificaciones antiguas", deleted_count)


@shared_task
def update_offer_status():
    """
    Actualiza el estado de las ofertas notificadas para saber si siguen activas
    """
    # Obtener notificaciones activas con más de 24 horas
    cutoff_date = timezone.now() - timezone.timedelta(hours=24)
    active_notifications = WatchdogNotification.objects.filter(is_active=True, notified_at__lt=cutoff_date)

    for notification in active_notifications:
        try:
            # Verificar si la oferta sigue activa
            response = requests.get(f"https://hodlhodl.com/api/v1/offers/{notification.offer_id}", timeout=6)

            # Manejar la respuesta basada en el estado
            response.raise_for_status()  # Lanzará excepciones para códigos 4xx/5xx

            # Si llegamos aquí, la respuesta fue exitosa (200 OK)
            offer_data = response.json().get("offer", {})
            if offer_data:
                notification.offer_details = {
                    "price": offer_data.get("price"),
                    "fee": offer_data.get("fee"),
                    "min_amount": offer_data.get("min_amount"),
                    "max_amount": offer_data.get("max_amount"),
                }
                notification.save()

        except requests.exceptions.HTTPError as e:
            exception_404 = 404
            if e.response.status_code == exception_404:
                # La oferta ya no existe
                notification.is_active = False
                notification.save()
            else:
                # Otro error HTTP (no 404)
                logger.exception(
                    "Error HTTP %s al actualizar estado de oferta %s",
                    e.response.status_code,
                    notification.offer_id,
                )
        except Exception:
            logger.exception("Error al actualizar estado de oferta %s", notification.offer_id)
