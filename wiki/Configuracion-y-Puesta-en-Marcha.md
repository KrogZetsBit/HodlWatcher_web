# Configuración y Puesta en Marcha

Esta sección describe cómo configurar HodlWatcher Web para desarrollo local y cómo desplegarlo en un entorno de producción utilizando Docker.

## Configuración Local

Sigue estos pasos para poner en marcha el proyecto en tu máquina local para desarrollo o pruebas. Se asume que tienes Python, pip y Git instalados.

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/KrogZetsBit/HodlWatcher_web.git
    cd HodlWatcher_web
    ```

2.  **Crear y Activar un Entorno Virtual:**
    Es altamente recomendable usar un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    # En Linux/macOS
    source venv/bin/activate
    # En Windows
    # .
env\Scriptsctivate
    ```

3.  **Instalar Dependencias:**
    Las dependencias se listan en archivos `requirements/*.txt`. Para desarrollo local, instala desde `local.txt`:
    ```bash
    pip install -r requirements/local.txt
    ```
    Esto instalará Django, Celery, y todas las demás librerías necesarias.

4.  **Configurar Variables de Entorno:**
    El proyecto utiliza variables de entorno para configuraciones sensibles o específicas del entorno. Cookiecutter-Django usa un archivo `.env` para esto.
    *   Crea un archivo `.env` en la raíz del proyecto copiando el ejemplo si existe (`.env.example`) o basándote en `config/settings/local.py`.
    *   Asegúrate de configurar al menos `DATABASE_URL` (por defecto SQLite para desarrollo local) y `REDIS_URL` (si Celery lo requiere para el message broker).
    *   Ejemplo de `DATABASE_URL` para SQLite (por defecto en `local.py` si no se especifica):
        ```
        DATABASE_URL=sqlite:///mydatabase.sqlite3
        ```
    *   Ejemplo de `REDIS_URL`:
        ```
        REDIS_URL=redis://localhost:6379/0
        ```
        (Necesitarás tener Redis corriendo localmente si no usas Docker para servicios de respaldo).

5.  **Aplicar Migraciones de Base de Datos:**
    Esto crea las tablas necesarias en tu base de datos.
    ```bash
    python manage.py migrate
    ```

6.  **Crear un Superusuario (Administrador):**
    Esto te permitirá acceder al panel de administración de Django.
    ```bash
    python manage.py createsuperuser
    ```
    Sigue las instrucciones para establecer un nombre de usuario, email y contraseña.

7.  **Ejecutar el Servidor de Desarrollo:**
    ```bash
    python manage.py runserver
    ```
    La aplicación debería estar disponible en `http://127.0.0.1:8000/`.

8.  **Ejecutar Celery (para tareas en segundo plano):**
    Las tareas de monitorización de HodlHodl se ejecutan con Celery. Necesitarás un message broker como Redis.
    *   **Worker de Celery:**
        ```bash
        celery -A config.celery_app worker -l info
        ```
    *   **Beat de Celery (para tareas programadas):**
        ```bash
        celery -A config.celery_app beat -l info
        ```
    Asegúrate de ejecutar estos comandos desde el directorio raíz del proyecto (donde está `manage.py`).

### Comandos Básicos Adicionales (del README)

*   **Verificar Tipos con Mypy:**
    ```bash
    mypy hodlwatcher
    ```
*   **Cobertura de Pruebas:**
    ```bash
    coverage run -m pytest
    coverage html
    # open htmlcov/index.html (en macOS)
    ```
*   **Ejecutar Pruebas con Pytest:**
    ```bash
    pytest
    ```

## Despliegue con Docker

El proyecto está configurado para ser desplegado utilizando Docker y Docker Compose, lo cual simplifica la gestión de los diferentes servicios (Django, PostgreSQL, Redis, Celery, Telegram Bot, Traefik).

La configuración de Docker se encuentra en el directorio `compose/` y los archivos principales de Docker Compose son `docker-compose.local.yml` (para desarrollo con Docker) y `docker-compose.production.yml` (para producción).

### Entorno Local con Docker

1.  **Construir las Imágenes y Levantar los Contenedores:**
    Desde el directorio raíz del proyecto:
    ```bash
    docker-compose -f docker-compose.local.yml build
    docker-compose -f docker-compose.local.yml up
    ```
    Esto iniciará la aplicación Django, PostgreSQL, Redis, Celery worker, Celery beat y el bot de Telegram, cada uno en su propio contenedor.

2.  **Aplicar Migraciones y Crear Superusuario (dentro del contenedor Django):**
    *   Encuentra el ID del contenedor de Django: `docker ps`
    *   Ejecuta los comandos dentro del contenedor:
        ```bash
        docker-compose -f docker-compose.local.yml exec django python manage.py migrate
        docker-compose -f docker-compose.local.yml exec django python manage.py createsuperuser
        ```

### Entorno de Producción con Docker

El despliegue en producción es similar pero utiliza `docker-compose.production.yml`. Este archivo está optimizado para producción e incluye servicios como Traefik para el proxy inverso.

1.  **Configuración de Variables de Entorno:**
    *   Asegúrate de que el archivo `.env` en la raíz del proyecto (o los archivos referenciados por `docker-compose.production.yml`, como `.envs/.production/.django` y `.envs/.production/.postgres`) contengan la configuración correcta para producción (ej. `SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, credenciales de base de datos seguras, `POSTGRES_PASSWORD`, configuraciones de email, API keys de Telegram, etc.).
    *   **Importante:** `DJANGO_DEBUG` debe estar configurado a `False` en producción.

2.  **Construir las Imágenes y Levantar los Contenedores:**
    ```bash
    docker-compose -f docker-compose.production.yml build
    docker-compose -f docker-compose.production.yml up -d # -d para modo detached
    ```

3.  **Operaciones Iniciales (si es el primer despliegue):**
    ```bash
    docker-compose -f docker-compose.production.yml exec django python manage.py migrate
    docker-compose -f docker-compose.production.yml exec django python manage.py createsuperuser
    docker-compose -f docker-compose.production.yml exec django python manage.py collectstatic --noinput # Recolectar archivos estáticos
    ```

### Servicios Incluidos en la Configuración de Docker (Producción Típica)

*   **`django`:** La aplicación web HodlWatcher.
*   **`postgres`:** La base de datos PostgreSQL.
*   **`redis`:** El broker de mensajes para Celery.
*   **`celeryworker`:** El worker de Celery que ejecuta las tareas de fondo.
*   **`celerybeat`:** El planificador de Celery que dispara tareas periódicas.
*   **`telegram_bot`:** El bot de Telegram corriendo en su propio contenedor.
*   **`traefik`:** Un proxy inverso moderno que maneja las solicitudes HTTP/HTTPS, certificados SSL (puede configurarse para Let's Encrypt), y dirige el tráfico al servicio `django`.
*   **`tor` (opcional):** Un proxy Tor que podría ser utilizado por la aplicación para realizar solicitudes externas de forma anónima.

Consulta la [documentación de Cookiecutter Django sobre Docker](https://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html) para obtener más detalles sobre la estructura y personalización del despliegue con Docker.
