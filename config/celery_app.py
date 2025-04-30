import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("hodelwatcher")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Schedule tasks
app.conf.beat_schedule = {
    "update-prices-every-5-minutes": {
        "task": "hodlwatcher.app.tasks.update_price_cache",
        "schedule": 60 * 5,  # 5 minutos
    },
    "update-payment_methods-every-month": {
        "task": "hodlwatcher.app.tasks.update_payment_methods",
        "schedule": crontab(hour=4, minute=0, day_of_month=14),  # A las 4 AM cada día 14 del mes
    },
    "update-currencies-every-month": {
        "task": "hodlwatcher.app.tasks.update_currencies",
        "schedule": crontab(hour=4, minute=0, day_of_month=14),  # A las 4 AM cada día 14 del mes
    },
    "check-watchdogs-every-1-minutes": {
        "task": "hodlwatcher.app.tasks.check_watchdogs",
        "schedule": 60 * 1,  # Cada 1 minutos
    },
    "clean-old-notifications-daily": {
        "task": "hodlwatcher.app.tasks.clean_old_notifications",
        "schedule": crontab(hour=3, minute=0),  # A las 3 AM cada día
    },
    "update-offer-status-weekly": {
        "task": "hodlwatcher.app.tasks.update_offer_status",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Se ejecuta cada domingo a las 3:00 AM
    },
}
