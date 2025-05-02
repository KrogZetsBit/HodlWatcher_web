import logging

from django.conf import settings
from django_yubin.message_views import TemplatedHTMLEmailMessageView

logger = logging.getLogger(__name__)


class WatchdogNotificationView(TemplatedHTMLEmailMessageView):
    subject_template_name = "emails/watchdog/subject.txt"
    body_template_name = "emails/watchdog/body.txt"
    html_body_template_name = "emails/watchdog/email_alert_watchdog.html"

    def __init__(self, watchdog, offers, fee):
        """
        Initializes the view with the watchdog and matching offers.

        Args:
            watchdog (InvestmentWatchdog): the watchdog that triggered the notification.
            offers (list): List of matching offers.
        """
        self.watchdog = watchdog
        self.offers = offers
        self.fee = fee
        super().__init__()

    def get_context_data(self, **kwargs):
        """
        Prepara el contexto para las plantillas de correo.
        """
        context = super().get_context_data(**kwargs)
        context["watchdog"] = self.watchdog
        context["offers"] = self.offers[:1]  # Limitamos a las 5 mejores ofertas
        context["fee"] = self.fee
        context["operation"] = "Compra" if self.watchdog.side == "buy" else "Venta"
        return context


class NotificationContactView(TemplatedHTMLEmailMessageView):
    subject_template_name = "emails/contact/subject_contact.txt"
    body_template_name = "emails/watchdog/body.txt"
    html_body_template_name = "emails/contact/email_confirm_contact.html"

    def __init__(self, form):
        """
        Initializes the view with the watchdog and matching offers.

        Args:
            watchdog (InvestmentWatchdog): the watchdog that triggered the notification.
            offers (list): List of matching offers.
        """
        self.form = form
        super().__init__()

    def get_context_data(self, **kwargs):
        """
        Prepara el contexto para las plantillas de correo.
        """
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class NotificationAdminContactView(TemplatedHTMLEmailMessageView):
    subject_template_name = "emails/contact/subject_admin_contact.txt"
    body_template_name = "emails/watchdog/body.txt"
    html_body_template_name = "emails/contact/email_admin_contact.html"


def send_watchdog_notification(watchdog, offers, fee):
    """
    Sends an email notification to the watchdog user
    with information about matching offers.

    Args:
        watchdog (InvestmentWatchdog): The watchdog that triggered the notification.
        offers (list): List of matched offers
    """
    try:
        # Instanciar y enviar el mensaje
        WatchdogNotificationView(watchdog, offers, fee).send(
            to=[watchdog.user.email], from_email=settings.DEFAULT_FROM_EMAIL
        )
    except Exception:
        logger.exception("Error al enviar correo de notificación")
        return False
    else:
        return True


def send_contact_email():
    try:
        # Instanciar y enviar el mensaje
        NotificationAdminContactView().send(to=[settings.DEFAULT_FROM_EMAIL], from_email=settings.DEFAULT_FROM_EMAIL)
    except Exception:
        logger.exception("Error al enviar correo de contacto")
        return False
    else:
        return True


def send_contact_confirmation_email(form):
    try:
        # Instanciar y enviar el mensaje
        NotificationContactView(form).send(to=[form["email"]], from_email=settings.DEFAULT_FROM_EMAIL)
    except Exception:
        logger.exception("Error al enviar correo de contacto")
        return False
    else:
        return True
