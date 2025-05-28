# Arquitectura y Módulos

HodlWatcher Web está construido utilizando el framework Django y sigue una arquitectura modular para organizar su código y funcionalidades. A continuación, se describen los principales componentes del proyecto:

## Aplicación Principal (`hodlwatcher/app`)

Este es el corazón de HodlWatcher. Contiene la lógica de negocio fundamental relacionada con la monitorización de ofertas y la gestión de alertas.

*   **Propósito Principal:**
    *   Permitir a los usuarios crear y gestionar "Watchdogs", que son criterios específicos para buscar ofertas de Bitcoin en HodlHodl.
    *   Monitorizar continuamente HodlHodl en segundo plano para encontrar ofertas que coincidan con los Watchdogs activos.
    *   Enviar notificaciones a los usuarios (vía Email y Telegram) cuando se detecta una oferta relevante.
    *   Proporcionar una interfaz para buscar y filtrar manualmente las ofertas actuales en HodlHodl.
    *   Gestionar la comunicación con el bot de Telegram.

*   **Componentes Clave:**
    *   `models.py`: Define las estructuras de datos como `InvestmentWatchdog` (para los criterios de alerta), `UsuarioTelegram` (para vincular usuarios de Django con usuarios de Telegram), `WatchdogNotification` (para registrar las notificaciones enviadas) y `ContactMessage` (para el formulario de contacto).
    *   `views.py` y `email_views.py`: Gestionan las solicitudes web para crear/listar Watchdogs, mostrar ofertas, y enviar correos electrónicos.
    *   `forms.py`: Define los formularios utilizados para la creación y edición de Watchdogs.
    *   `tasks.py`: Contiene las tareas asíncronas (ejecutadas por Celery) responsables de la monitorización periódica de HodlHodl (`check_watchdogs`), actualización de caché de precios/métodos de pago, y limpieza de notificaciones antiguas.
    *   `utils.py`: Probablemente contiene funciones de utilidad para interactuar con la API de HodlHodl y procesar los Watchdogs.
    *   `management/commands/run_telegram_bot.py`: Script para ejecutar el bot de Telegram.

## Módulo de Usuarios (`hodlwatcher/users`)

Esta aplicación gestiona todo lo relacionado con las cuentas de usuario, autenticación y perfiles.

*   **Propósito Principal:**
    *   Permitir el registro de nuevos usuarios.
    *   Gestionar el inicio y cierre de sesión (autenticación).
    *   Permitir a los usuarios restablecer sus contraseñas.
    *   Manejar los perfiles de usuario, incluyendo la configuración de la autenticación de dos factores (2FA).
    *   Proporcionar la infraestructura para la gestión de usuarios por parte de los administradores.

*   **Componentes Clave:**
    *   `models.py`: Define el modelo `User` personalizado, que probablemente extiende el modelo de usuario base de Django.
    *   `forms.py`: Contiene formularios para el registro, inicio de sesión, cambio de contraseña y edición de perfil.
    *   `views.py`: Implementa la lógica para las vistas de autenticación y gestión de perfiles.
    *   `adapters.py`: Se utiliza para personalizar el comportamiento de `django-allauth`, que maneja gran parte de la lógica de autenticación, incluyendo el registro, inicio de sesión, gestión de email y 2FA.

## Módulo de FAQ (`hodlwatcher/faq`)

Esta aplicación se encarga de la sección de Preguntas Frecuentes (FAQ) del sitio.

*   **Propósito Principal:**
    *   Permitir a los administradores crear, gestionar y categorizar preguntas frecuentes y sus respuestas.
    *   Mostrar las FAQs a los usuarios de una manera organizada y fácil de navegar.
    *   Soportar la traducción de las FAQs a múltiples idiomas (inglés, español, francés).

*   **Componentes Clave:**
    *   `models.py`: Define los modelos `FAQ` (para cada pregunta y respuesta) y `FAQCategory` (para agrupar FAQs).
    *   `views.py`: Controla la visualización de la lista de categorías de FAQs y las FAQs individuales.
    *   `admin.py`: Permite la gestión de FAQs desde la interfaz de administración de Django.
    *   `translation.py`: Facilita la internacionalización del contenido de las FAQs.

## Configuración del Proyecto (`config/`)

Este directorio contiene los archivos de configuración globales para el proyecto Django.

*   **Propósito Principal:**
    *   Definir los ajustes del proyecto, como la configuración de la base de datos, las aplicaciones instaladas, las plantillas, los middlewares, etc.
    *   Gestionar diferentes entornos de configuración (desarrollo local, producción, pruebas).
    *   Configurar la integración con Celery para tareas en segundo plano.
    *   Definir las URLs raíz del proyecto.

*   **Componentes Clave:**
    *   `settings/base.py`, `settings/local.py`, `settings/production.py`, `settings/test.py`: Archivos de configuración para diferentes entornos.
    *   `urls.py`: El archivo principal de enrutamiento de URLs del proyecto.
    *   `celery_app.py`: Configuración de la instancia de Celery.

## Configuración de Docker (`compose/`)

Este directorio alberga los archivos necesarios para construir y orquestar los servicios del proyecto utilizando Docker y Docker Compose.

*   **Propósito Principal:**
    *   Facilitar la creación de entornos de desarrollo y producción consistentes y reproducibles.
    *   Definir cómo se construyen las imágenes de Docker para los diferentes componentes (aplicación Django, base de datos PostgreSQL, bot de Telegram, proxy inverso Traefik, etc.).
    *   Orquestar el despliegue y la interconexión de estos servicios.

*   **Componentes Clave:**
    *   `local/`: Contiene Dockerfiles y scripts para el entorno de desarrollo local.
        *   `django/Dockerfile`: Define la imagen para la aplicación Django.
        *   `telegram/Dockerfile`: Define la imagen para el bot de Telegram.
    *   `production/`: Contiene Dockerfiles y scripts para el entorno de producción.
        *   `django/Dockerfile`: Define la imagen de producción para Django.
        *   `postgres/Dockerfile`: Define la imagen para la base de datos PostgreSQL.
        *   `telegram/Dockerfile`: Define la imagen de producción para el bot de Telegram.
        *   `traefik/Dockerfile`: Define la imagen para el proxy Traefik.
        *   `tor/Dockerfile`: Define la imagen para un proxy Tor.
    *   `docker-compose.local.yml`, `docker-compose.production.yml`: Archivos de Docker Compose que definen los servicios, redes y volúmenes para los respectivos entornos.
