import logging

from asgiref.sync import sync_to_async
from constance import config
from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from hodlwatcher.app.models import Configuracion
from hodlwatcher.app.models import InvestmentWatchdog
from hodlwatcher.app.models import UsuarioTelegram

# Configurar logs
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Inicia el bot de Telegram para monitoreo de inversiones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Ejecutar el bot en modo debug",
        )

    def get_usuario_by_chat_id(self, chat_id):
        """Obtiene un usuario de Telegram por su chat_id."""
        try:
            return UsuarioTelegram.objects.get(chat_id=chat_id)
        except UsuarioTelegram.DoesNotExist:
            return None

    def get_or_create_user(self, chat_id, username):
        """Obtiene o crea un usuario de Telegram."""
        return UsuarioTelegram.objects.get_or_create(chat_id=chat_id, defaults={"username": username})

    def get_user_by_username(self, username):
        """Obtiene un usuario de Telegram por su username."""
        try:
            return UsuarioTelegram.objects.get(username=username)
        except UsuarioTelegram.DoesNotExist:
            return None

    def get_user_watchdogs(self, chat_id):
        """Obtiene los watchdogs asociados al usuario de Telegram."""
        usuario = self.get_usuario_by_chat_id(chat_id)
        logger.info("get_user_watchdogs: usuario encontrado=%s", usuario is not None)

        if not usuario:
            return []

        # Verificar si el modelo InvestmentWatchdog tiene relación directa con UsuarioTelegram
        has_direct_relation = hasattr(InvestmentWatchdog, "usuario_telegram")
        logger.info("get_user_watchdogs: relación directa=%s", has_direct_relation)

        if has_direct_relation:
            # Usar la relación directa si existe
            watchdogs = InvestmentWatchdog.objects.filter(usuario_telegram=usuario)
        else:
            # Buscar a través de la configuración si no hay relación directa
            config = Configuracion.objects.filter(user_telegram=usuario).first()
            logger.info("get_user_watchdogs: configuración encontrada=%s", config is not None)
            watchdogs = InvestmentWatchdog.objects.filter(user=config.user) if config else []

        logger.info("get_user_watchdogs: watchdogs encontrados=%s", len(watchdogs))
        return watchdogs

    def create_or_update_watchdog(self, chat_id, rate_fee: float, **kwargs) -> bool:
        """Crea o actualiza un watchdog con el rate_fee especificado."""
        usuario = self.get_usuario_by_chat_id(chat_id)
        if not usuario:
            return False

        # Actualizar también el rate_fee base del usuario como referencia
        usuario.rate_fee = rate_fee
        usuario.save()

        # Si hay watchdogs existentes, crear o actualizar según el caso
        watchdogs = self.get_user_watchdogs(chat_id)

        # Si no hay kwargs específicos, crear o actualizar un watchdog predeterminado
        # usando valores por defecto del modelo
        if not kwargs and not watchdogs.exists():
            # Obtener usuario Django a través de la configuración
            config = Configuracion.objects.filter(user_telegram=usuario).first()
            if not config:
                return False

            # Crear un watchdog predeterminado
            InvestmentWatchdog.objects.create(
                user=config.user,
                rate_fee=rate_fee,
                usuario_telegram=usuario,
                amount=100,  # Valor predeterminado
            )
            return True
        if kwargs:
            # Crear/actualizar watchdog con parámetros específicos
            # Implementación depende de requisitos específicos
            pass
        elif watchdogs.exists():
            # Actualizar todos los watchdogs existentes
            watchdogs.update(rate_fee=rate_fee)
            return True

        return False

    def toggle_alertas_watchdog(self, chat_id, estado):
        """Activa/desactiva alertas de watchdog para un usuario."""
        try:
            usuario = UsuarioTelegram.objects.get(chat_id=chat_id)
            usuario.recibir_alertas_watchdog = estado
            usuario.save()
        except UsuarioTelegram.DoesNotExist:
            return False
        else:
            return True

    def toggle_watchdog_by_index(self, chat_id, idx):
        """Cambia el estado de un watchdog específico."""
        watchdogs = list(self.get_user_watchdogs(chat_id))
        if 0 <= idx < len(watchdogs):
            watchdog = watchdogs[idx]
            watchdog.active = not watchdog.active  # Usar 'active' según el modelo
            watchdog.save()
            return watchdog
        return None

    # Convertir funciones síncronas a asíncronas
    get_or_create_user_async = sync_to_async(get_or_create_user)
    get_usuario_by_chat_id_async = sync_to_async(get_usuario_by_chat_id)
    create_or_update_watchdog_async = sync_to_async(create_or_update_watchdog)
    toggle_alertas_watchdog_async = sync_to_async(toggle_alertas_watchdog)
    get_user_watchdogs_async = sync_to_async(get_user_watchdogs)
    toggle_watchdog_by_index_async = sync_to_async(toggle_watchdog_by_index)

    # Definir manejadores de comandos
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Comando /start: Registra al usuario en la base de datos."""
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Usuario desconocido"

        try:
            _, created = await self.get_or_create_user_async(chat_id, username)

            if created:
                message = f"👋 ¡Hola {username}! Te has registrado correctamente."
                logger.info("Nuevo usuario registrado: %s (ID: %s)", username, chat_id)
            else:
                message = f"👋 ¡Hola {username}! Ya estabas registrado."
                logger.info("Usuario existente conectado: %s (ID: %s)", username, chat_id)

            await update.message.reply_text(message)
        except Exception:
            logger.exception("Error en comando start")
            await update.message.reply_text("❌ Error al procesar tu solicitud. Por favor, intenta de nuevo.")

    async def modificar_rate_fee(self, update: Update, context: CallbackContext) -> None:
        """Comando /ratefee: Crea o actualiza watchdogs con el rate_fee especificado."""
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Usuario desconocido"

        if not context.args:
            # Si no hay argumentos, mostrar los rate_fee actuales
            watchdogs = await self.get_user_watchdogs_async(chat_id)
            if watchdogs:
                mensaje = "📊 *Rate Fees actuales:*\n\n"
                for i, watchdog in enumerate(watchdogs, 1):
                    mensaje += f"{i}. {float(watchdog.rate_fee)}%\n"
                await update.message.reply_text(mensaje, parse_mode="Markdown")
            else:
                await update.message.reply_text(
                    "❌ No tienes rate_fees configurados. Usa /ratefee [valor] para configurar uno."
                )
            return

        try:
            nuevo_rate_fee = float(context.args[0])
            if nuevo_rate_fee < 0:
                await update.message.reply_text("❌ El rate_fee no puede ser un valor negativo.")
                return

            actualizado = await self.create_or_update_watchdog_async(chat_id, nuevo_rate_fee)
            if actualizado:
                logger.info("Usuario %s modificó el rate_fee a %s%", username, nuevo_rate_fee)
                await update.message.reply_text(f"✅ El rate_fee ha sido actualizado a {nuevo_rate_fee}%.")
            else:
                await update.message.reply_text("❌ No se pudo actualizar el rate fee. Verifica que estés registrado.")

        except ValueError:
            await update.message.reply_text("❌ Debes proporcionar un número válido. Ejemplo: /ratefee 5")
        except Exception:
            logger.exception("Error al modificar el rate_fee")
            await update.message.reply_text("❌ Ocurrió un error al modificar el rate_fee.")

    async def alerta(self, update: Update, context: CallbackContext) -> None:
        """Comando /alerta: Envía una alerta con los rate_fee configurados."""
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Usuario desconocido"
        logger.info("Usuario %s solicitó una alerta", username)

        try:
            watchdogs = await self.get_user_watchdogs_async(chat_id)

            if watchdogs:
                mensaje = "🚨 *ALERTA DE RATE FEES:*\n\n"

                for i, watchdog in enumerate(watchdogs, 1):
                    mensaje += (
                        f"{i}. *Watchdog {watchdog.id}*\n"
                        f"   Moneda: {watchdog.currency} - {watchdog.asset_code}\n"
                        f"   Rate Fee: {float(watchdog.rate_fee)}%\n"
                        f"   Estado: {'Activo' if watchdog.active else 'Inactivo'}\n\n"
                    )

                await update.message.reply_text(mensaje, parse_mode="Markdown")
            else:
                # Si no hay watchdogs, mostrar el rate_fee base del usuario
                usuario = await self.get_usuario_by_chat_id_async(chat_id)
                if usuario:
                    mensaje = (
                        f"🚨 ALERTA: Tu rate_fee base es {usuario.rate_fee}%. No tienes watchdogs configurados. 🚨"
                    )
                    await update.message.reply_text(mensaje)
                else:
                    await update.message.reply_text("❌ No hay rate_fees configurados. Usa /start primero.")
        except Exception:
            logger.exception("Error en comando alerta")
            await update.message.reply_text("❌ Error al generar la alerta.")

    async def toggle_watchdog(self, update: Update, context: CallbackContext) -> None:
        """Comando /watchdog: Activa o desactiva las notificaciones de watchdog."""
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Usuario desconocido"

        if not context.args or context.args[0].lower() not in ["on", "off"]:
            await update.message.reply_text(
                "❌ Debes especificar si quieres activar o desactivar las alertas: /watchdog on o /watchdog off"
            )
            return

        estado = context.args[0].lower() == "on"

        try:
            actualizado = await self.toggle_alertas_watchdog_async(chat_id, estado)
            if actualizado:
                estado_texto = "activadas" if estado else "desactivadas"
                logger.info("Usuario %s %s las alertas de watchdog", username, estado_texto)
                await update.message.reply_text(f"✅ Las alertas de watchdog han sido {estado_texto}.")
            else:
                await update.message.reply_text("❌ No se encontró tu usuario. Por favor, usa /start primero.")
        except Exception:
            logger.exception("Error al cambiar estado de alertas")
            await update.message.reply_text("❌ Ocurrió un error al cambiar el estado de las alertas.")

    async def estado_watchdog(self, update: Update, context: CallbackContext) -> None:
        """Comando /estado: Muestra el estado actual de las notificaciones."""
        chat_id = update.effective_chat.id

        try:
            usuario = await self.get_usuario_by_chat_id_async(chat_id)
            if usuario:
                estado = "activadas" if usuario.recibir_alertas_watchdog else "desactivadas"

                # Obtener los watchdogs para mostrar sus rate_fees
                watchdogs = await self.get_user_watchdogs_async(chat_id)

                mensaje = f"📊 *Estado actual*\n- Alertas de watchdog: {estado}\n- Rate Fee base: {usuario.rate_fee}%\n"

                if watchdogs:
                    mensaje += "\n*Watchdogs configurados:*\n"
                    for i, watchdog in enumerate(watchdogs, 1):
                        mensaje += (
                            f"{i}. {watchdog.currency}-{watchdog.asset_code}: "
                            f"{float(watchdog.rate_fee)}% "
                            f"({'Activo' if watchdog.active else 'Inactivo'})\n"
                        )

                await update.message.reply_text(mensaje, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ No se encontró tu usuario. Por favor, usa /start primero.")
        except Exception:
            logger.exception("Error al obtener estado")
            await update.message.reply_text("❌ Ocurrió un error al obtener el estado.")

    async def listar_watchdogs(self, update: Update, context: CallbackContext) -> None:
        """Comando /miswatchdogs: Lista los watchdogs configurados por el usuario."""
        chat_id = update.effective_chat.id
        logger.info("Solicitando watchdogs para chat_id: %s", chat_id)

        try:
            usuario = await self.get_usuario_by_chat_id_async(chat_id)
            logger.info("Usuario encontrado: %s", usuario is not None)

            watchdogs = await self.get_user_watchdogs_async(chat_id)
            logger.info("Watchdogs encontrados: %s", len(watchdogs) if watchdogs else 0)

            if watchdogs:
                mensaje = "🔍 *Tus Investment Watchdogs:*\n\n"

                for i, watchdog in enumerate(watchdogs, 1):
                    estado = "✅ Activo" if watchdog.active else "❌ Inactivo"  # Usar 'active' según el modelo

                    # Adaptar a los campos del modelo real
                    side = "I want to buy" if watchdog.side == "sell" else "I want to sell"
                    mensaje += (
                        f"{i}. *Watchdog {watchdog.id}*\n"
                        f"   Moneda: {watchdog.currency} - {watchdog.asset_code}\n"
                        f"   Tipo: {side}\n"
                        f"   Rate Fee: {float(watchdog.rate_fee)}%\n"
                        f"   Monto: {watchdog.amount}\n"
                        f"   Estado: {estado}\n\n"
                    )

                await update.message.reply_text(mensaje, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ No tienes watchdogs configurados o tu cuenta no está vinculada.")

        except Exception:
            logger.exception("Error al listar watchdogs")
            await update.message.reply_text("❌ Ocurrió un error al obtener tus watchdogs.")

    async def toggle_watchdog_estado(self, update: Update, context: CallbackContext) -> None:
        """Comando /togglewatchdog: Activa o desactiva un watchdog específico."""
        chat_id = update.effective_chat.id

        if not context.args:
            await update.message.reply_text(
                "❌ Debes proporcionar el número del watchdog que quieres activar/desactivar. "
                "Usa /miswatchdogs para ver la lista numerada."
            )
            return

        try:
            idx = int(context.args[0]) - 1
            watchdog = await self.toggle_watchdog_by_index_async(chat_id, idx)

            if watchdog:
                estado = "activado" if watchdog.active else "desactivado"  # Usar 'active' según el modelo
                await update.message.reply_text(
                    f"✅ El watchdog #{idx + 1} ha sido {estado}.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ Número de watchdog inválido. Usa /miswatchdogs para ver la lista numerada."
                )

        except ValueError:
            await update.message.reply_text("❌ Debes proporcionar un número válido.")
        except Exception:
            logger.exception("Error al cambiar estado de watchdog")
            await update.message.reply_text("❌ Ocurrió un error al cambiar el estado del watchdog.")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Comando /help: Muestra la ayuda del bot."""
        help_text = (
            "📋 *Comandos disponibles:*\n\n"
            "/start - Registrarse en el sistema\n"
            "/ratefee - Consultar o modificar los rate fees configurados\n"
            "/watchdog on|off - Activar o desactivar todas las alertas de watchdogs\n"
            "/miswatchdogs - Lista tus watchdogs configurados\n"
            "/togglewatchdog [número] - Activa/desactiva un watchdog específico\n"
            "/estado - Ver el estado actual de tus alertas y rate fees\n"
            "/alerta - Enviar una alerta con tus rate fees configurados\n"
            "/help - Mostrar este mensaje de ayuda"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    def handle(self, *args, **options):
        log_level = logging.DEBUG if options["debug"] else logging.INFO
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=log_level,
        )
        # Validar token
        token = config.TELEGRAM_BOT_TOKEN
        if not token:
            self.stdout.write(self.style.ERROR("Error: TELEGRAM_BOT_TOKEN no está configurado"))
            return

        self.stdout.write(self.style.SUCCESS("Iniciando bot de Telegram..."))
        if options["debug"]:
            self.stdout.write(self.style.WARNING("Ejecutando en modo DEBUG"))

        # Manejador de errores
        async def error_handler(update: Update, context: CallbackContext):
            logger.error("Error manejando la actualización %s: %s", update, context.error)
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Ocurrió un error al procesar tu solicitud. Intenta nuevamente."
                )

        # Inicializar la aplicación
        try:
            app = Application.builder().token(token).build()

            # Registrar los manejadores de comandos
            app.add_handler(CommandHandler("start", self.start))
            app.add_handler(CommandHandler("ratefee", self.modificar_rate_fee))
            app.add_handler(CommandHandler("alerta", self.alerta))
            app.add_handler(CommandHandler("help", self.help_command))
            app.add_handler(CommandHandler("watchdog", self.toggle_watchdog))
            app.add_handler(CommandHandler("estado", self.estado_watchdog))
            app.add_handler(CommandHandler("miswatchdogs", self.listar_watchdogs))
            app.add_handler(CommandHandler("togglewatchdog", self.toggle_watchdog_estado))

            # Configurar manejador de errores
            app.add_error_handler(error_handler)

            self.stdout.write(self.style.SUCCESS("✅ Bot de Telegram iniciado correctamente"))

            # Iniciar el bot
            app.run_polling()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al iniciar el bot: {e}"))
            logger.exception("Error fatal")
