# Características Principales

HodlWatcher Web ofrece un conjunto de herramientas potentes para ayudarte a no perder nunca una oportunidad de trade en HodlHodl. A continuación, se detallan sus características más importantes:

### 1. Monitorización Automatizada de HodlHodl
*   **Descripción:** La aplicación revisa continuamente (24/7) las ofertas de compra y venta de Bitcoin en HodlHodl.
*   **Implementación a Alto Nivel:**
    *   Se utilizan tareas programadas (Celery tasks) definidas en `hodlwatcher/app/tasks.py` (ej. `check_watchdogs`).
    *   Estas tareas consultan periódicamente la API de HodlHodl (o una fuente de datos similar) para obtener las ofertas más recientes.
    *   La lógica para procesar estas ofertas y compararlas con los criterios de los usuarios reside principalmente en `hodlwatcher/app/utils.py` y es invocada por las tareas Celery.

### 2. "Watchdogs" Personalizables
*   **Descripción:** Los usuarios pueden crear "Watchdogs" (alertas) especificando criterios detallados para las ofertas que les interesan.
*   **Criterios Soportados:**
    *   **Operación:** Compra o Venta.
    *   **Activo:** Bitcoin (BTC).
    *   **Moneda:** EUR, USD, y otras soportadas por HodlHodl.
    *   **Cantidad:** El volumen de BTC deseado.
    *   **Método de Pago:** Filtro por métodos preferidos (ej. SEPA, Revolut, etc.).
    *   **Tasa de Fee Máxima:** Porcentaje máximo de comisión de la oferta.
*   **Implementación a Alto Nivel:**
    *   El modelo `InvestmentWatchdog` en `hodlwatcher/app/models.py` almacena estos criterios.
    *   Los formularios en `hodlwatcher/app/forms.py` permiten a los usuarios introducir estos datos.
    *   Las vistas en `hodlwatcher/app/views.py` gestionan la creación, visualización y modificación de los Watchdogs.

### 3. Notificaciones Instantáneas (Telegram y Email)
*   **Descripción:** Cuando una oferta coincide con un Watchdog activo, el usuario recibe una notificación inmediata.
*   **Canales:**
    *   **Telegram:** Mensajes directos al bot de Telegram vinculado.
    *   **Email:** Correos electrónicos a la dirección registrada por el usuario.
*   **Implementación a Alto Nivel:**
    *   **Email:**
        *   La funcionalidad de envío de correos se maneja probablemente a través de las funciones de Django y puede estar en `hodlwatcher/app/email_views.py` o `hodlwatcher/app/utils.py`.
        *   Se utilizan plantillas de correo (en `hodlwatcher/templates/emails/`) para formatear los mensajes.
    *   **Telegram:**
        *   La integración con Telegram se gestiona a través de un bot (definido en `hodlwatcher/app/management/commands/run_telegram_bot.py`).
        *   Se utiliza una librería como `python-telegram-bot`.
        *   El modelo `UsuarioTelegram` (`hodlwatcher/app/models.py`) vincula la cuenta de HodlWatcher con el ID de chat de Telegram del usuario.
        *   Las notificaciones se envían desde `hodlwatcher/app/utils.py` o tareas Celery al detectar una coincidencia.
    *   El modelo `WatchdogNotification` (`hodlwatcher/app/models.py`) registra las notificaciones enviadas.

### 4. Buscador Manual de Ofertas
*   **Descripción:** Además de las alertas automáticas, los usuarios pueden buscar y filtrar manualmente las ofertas activas en HodlHodl directamente desde la aplicación.
*   **Implementación a Alto Nivel:**
    *   Existe una vista específica, probablemente `BuscadorView` mencionada en `hodlwatcher/app/tasks.py` y definida en `hodlwatcher/app/views.py`.
    *   Esta vista interactúa con la API de HodlHodl para obtener y mostrar las ofertas.
    *   Puede incluir funcionalidades de caché (`update_price_cache`, `update_payment_methods`, `update_currencies` en `tasks.py`) para mejorar el rendimiento y reducir las llamadas a la API.

### 5. Cuentas de Usuario Seguras
*   **Descripción:** La plataforma ofrece un sistema robusto para la gestión de cuentas de usuario.
*   **Funcionalidades:**
    *   Registro (Sign Up)
    *   Inicio de Sesión (Sign In)
    *   Restablecimiento de Contraseña
    *   Gestión de Perfil
*   **Implementación a Alto Nivel:**
    *   Principalmente gestionado por el módulo `hodlwatcher/users/` y la librería `django-allauth`.
    *   El modelo `User` (`hodlwatcher/users/models.py`) define los datos del usuario.
    *   Las vistas y formularios en `hodlwatcher/users/` y las proporcionadas por `django-allauth` manejan los flujos de autenticación.

### 6. Seguridad Mejorada con Autenticación de Dos Factores (2FA)
*   **Descripción:** Los usuarios pueden proteger sus cuentas añadiendo una capa extra de seguridad con 2FA.
*   **Métodos Soportados:**
    *   Aplicaciones de Autenticación (ej. Google Authenticator, Authy).
    *   Llaves de Seguridad (ej. YubiKey).
    *   Códigos de Recuperación.
*   **Implementación a Alto Nivel:**
    *   Esta funcionalidad es proporcionada en gran medida por `django-allauth`, configurada dentro del módulo `hodlwatcher/users/`.
    *   La configuración específica puede encontrarse en `settings/base.py` (relacionada con `allauth`) y las plantillas de `django-allauth` personalizadas en `hodlwatcher/templates/account/`.

### 7. Bot de Telegram Inteligente
*   **Descripción:** Un bot de Telegram interactivo para gestionar aspectos de HodlWatcher.
*   **Funcionalidades del Bot:**
    *   Vincular de forma segura la cuenta de Telegram con la cuenta de HodlWatcher.
    *   Recibir alertas de ofertas directamente en el chat.
    *   Gestionar Watchdogs (crear, ver, activar/desactivar - *según el README, aunque la implementación exacta requeriría revisar el código del bot*).
    *   Consultar comisiones configuradas.
    *   Obtener ayuda.
*   **Implementación a Alto Nivel:**
    *   El código del bot se encuentra en `hodlwatcher/app/management/commands/run_telegram_bot.py`.
    *   Utiliza una librería como `python-telegram-bot` para interactuar con la API de Telegram.
    *   Se comunica con el resto de la aplicación Django para acceder a los datos del usuario y los Watchdogs. El modelo `UsuarioTelegram` es clave para esta vinculación.

### 8. Soporte Multi-idioma
*   **Descripción:** La interfaz de la aplicación está disponible en Inglés, Español y Francés.
*   **Implementación a Alto Nivel:**
    *   Utiliza el sistema de internacionalización (i18n) y localización (l10n) de Django.
    *   Archivos de traducción (`.po`, `.mo`) se encuentran en el directorio `locale/`.
    *   Las cadenas de texto en las plantillas (`.html`) y el código Python (`.py`) están marcadas para traducción (ej. `{% trans "Texto" %}` o `_("Texto")`).
    *   El módulo `hodlwatcher/faq/translation.py` y las migraciones que añaden campos traducidos (ej. `0002_faq_answer_fr_...`) confirman esto para la app de FAQ.

### 9. Sección de FAQ
*   **Descripción:** Una sección con preguntas frecuentes para ayudar a los usuarios.
*   **Implementación a Alto Nivel:**
    *   Gestionada por la aplicación `hodlwatcher/faq/`.
    *   Los modelos `FAQ` y `FAQCategory` (`hodlwatcher/faq/models.py`) almacenan el contenido.
    *   Las vistas en `hodlwatcher/faq/views.py` muestran las FAQs.
    *   Soporta múltiples idiomas.

### 10. Formulario de Contacto
*   **Descripción:** Permite a los usuarios enviar mensajes o consultas a los administradores del sitio.
*   **Implementación a Alto Nivel:**
    *   El modelo `ContactMessage` en `hodlwatcher/app/models.py` almacena los mensajes.
    *   Un formulario (probablemente en `hodlwatcher/app/forms.py`) para la entrada de datos.
    *   Una vista en `hodlwatcher/app/views.py` para procesar y guardar el mensaje, y posiblemente notificar a los administradores.

### 11. Panel de Administración
*   **Descripción:** Una interfaz para que los administradores gestionen la plataforma (usuarios, watchdogs, FAQs, etc.).
*   **Implementación a Alto Nivel:**
    *   Utiliza el panel de administración incorporado de Django.
    *   Los archivos `admin.py` en cada aplicación (`hodlwatcher/app/admin.py`, `hodlwatcher/users/admin.py`, `hodlwatcher/faq/admin.py`) registran los modelos y personalizan cómo se muestran en el panel de administración.
