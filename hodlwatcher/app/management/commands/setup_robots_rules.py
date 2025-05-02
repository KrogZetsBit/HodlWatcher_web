# src/main/management/commands/setup_robots_rules.py
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from robots.models import Rule
from robots.models import Url


class Command(BaseCommand):
    help = "Configura las reglas de robots.txt para el sitio"

    def handle(self, *args, **options):
        # Obtener o crear el sitio principal
        site, _ = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={
                "domain": settings.DOMAIN,
                "name": settings.APP_SLUG,
            },
        )

        # Crear regla principal para todos los robots
        rule, _ = Rule.objects.get_or_create(robot="*")
        rule.sites.add(site)

        # Permitir acceso a todo el sitio
        allowed_url, _ = Url.objects.get_or_create(pattern="/")
        rule.allowed.add(allowed_url)

        # Bloquear acceso al panel de administración
        admin_url, _ = Url.objects.get_or_create(pattern="/admin/")
        rule.disallowed.add(admin_url)

        admin_no_slash_url, _ = Url.objects.get_or_create(pattern="/admin")
        rule.disallowed.add(admin_no_slash_url)

        # Bloquear acceso a las rutas de autenticación
        login_url, _ = Url.objects.get_or_create(pattern="/accounts/login/")
        rule.disallowed.add(login_url)

        signup_url, _ = Url.objects.get_or_create(pattern="/accounts/signup/")
        rule.disallowed.add(signup_url)

        accounts_url, _ = Url.objects.get_or_create(pattern="/accounts/")
        rule.disallowed.add(accounts_url)

        self.stdout.write(self.style.SUCCESS("Reglas de robots.txt configuradas correctamente"))
