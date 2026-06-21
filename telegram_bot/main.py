import os
import logging
from telegram import BotCommand, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from handlers.auth import cmd_start, cmd_login, cmd_logout, cmd_registro
from handlers.album import cmd_mi_album, cmd_mi_album_ids, cmd_agregar, cmd_eliminar_figurita
from handlers.usuarios import cmd_faltantes, cmd_agregar_faltante, cmd_usuarios
from handlers.publicaciones import (
    cmd_publicaciones,
    cmd_publicaciones_id,
    cmd_mis_publicaciones,
    cmd_mis_publicaciones_id,
    cmd_publicar,
    cmd_retirar,
    cmd_sugerencias,
)
from handlers.intercambios import (
    cmd_intercambios,
    cmd_proponer,
    cmd_aceptar_intercambio,
    cmd_rechazar_intercambio,
)
from handlers.subastas import (
    cmd_subastas,
    cmd_crear_subasta,
    cmd_ofertar,
    cmd_cancelar_subasta,
    cmd_mis_subastas,
)
from handlers.maestro import cmd_buscar, cmd_equipos
from handlers.admin import cmd_estadisticas

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


COMANDOS = [
    BotCommand("start",                "Ver todos los comandos"),
    BotCommand("login",                "Iniciar sesión — /login email contraseña"),
    BotCommand("logout",               "Cerrar sesión"),
    BotCommand("registro",             "Crear cuenta — /registro nombre email contraseña"),
    BotCommand("mi_album",             "Ver mis figuritas"),
    BotCommand("mi_album_ids",         "Ver mis figuritas con IDs"),
    BotCommand("agregar",              "Agregar al álbum — /agregar numero cantidad"),
    BotCommand("eliminar_figurita",    "Eliminar del álbum — /eliminar_figurita id"),
    BotCommand("faltantes",            "Ver mis faltantes"),
    BotCommand("agregar_faltante",     "Marcar faltante — /agregar_faltante numero"),
    BotCommand("publicaciones",        "Ver publicaciones de otros usuarios"),
    BotCommand("publicaciones_id",     "Ver publicaciones de otros con IDs"),
    BotCommand("mis_publicaciones",    "Ver mis publicaciones"),
    BotCommand("mis_publicaciones_id", "Ver mis publicaciones con IDs"),
    BotCommand("publicar",             "Publicar figurita — /publicar id tipo cantidad"),
    BotCommand("retirar",              "Retirar publicación — /retirar id"),
    BotCommand("sugerencias",          "Ver sugerencias que cubren mis faltantes"),
    BotCommand("intercambios",         "Ver mis intercambios"),
    BotCommand("proponer",             "Proponer intercambio — /proponer usuario_id ofrecida solicitada"),
    BotCommand("aceptar_intercambio",  "Aceptar intercambio — /aceptar_intercambio id"),
    BotCommand("rechazar_intercambio", "Rechazar intercambio — /rechazar_intercambio id"),
    BotCommand("subastas",             "Ver subastas activas"),
    BotCommand("mis_subastas",         "Ver mis subastas"),
    BotCommand("crear_subasta",        "Crear subasta — /crear_subasta publicacion_id horas"),
    BotCommand("ofertar",              "Ofertar en subasta — /ofertar subasta_id figurita_id"),
    BotCommand("cancelar_subasta",     "Cancelar subasta — /cancelar_subasta id"),
    BotCommand("buscar",               "Buscar figurita en maestro — /buscar numero"),
    BotCommand("equipos",              "Listar equipos del álbum"),
    BotCommand("usuarios",             "Ver usuarios registrados"),
    BotCommand("estadisticas",         "Estadísticas del sistema (solo admin)"),
]


async def post_init(application):
    await application.bot.set_my_commands(COMANDOS)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Excepción en handler:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            f"❌ Error interno: {context.error}\n"
            "Si el problema persiste, contactá al administrador."
        )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN no está definido en el entorno.")

    app = ApplicationBuilder().token(token).post_init(post_init).build()

    # Auth
    app.add_handler(CommandHandler("start",                cmd_start))
    app.add_handler(CommandHandler("login",                cmd_login))
    app.add_handler(CommandHandler("logout",               cmd_logout))
    app.add_handler(CommandHandler("registro",             cmd_registro))

    # Album
    app.add_handler(CommandHandler("mi_album",             cmd_mi_album))
    app.add_handler(CommandHandler("mi_album_ids",         cmd_mi_album_ids))
    app.add_handler(CommandHandler("agregar",              cmd_agregar))
    app.add_handler(CommandHandler("eliminar_figurita",    cmd_eliminar_figurita))

    # Faltantes / Usuarios
    app.add_handler(CommandHandler("faltantes",            cmd_faltantes))
    app.add_handler(CommandHandler("agregar_faltante",     cmd_agregar_faltante))
    app.add_handler(CommandHandler("usuarios",             cmd_usuarios))

    # Publicaciones
    app.add_handler(CommandHandler("publicaciones",        cmd_publicaciones))
    app.add_handler(CommandHandler("publicaciones_id",     cmd_publicaciones_id))
    app.add_handler(CommandHandler("mis_publicaciones",    cmd_mis_publicaciones))
    app.add_handler(CommandHandler("mis_publicaciones_id", cmd_mis_publicaciones_id))
    app.add_handler(CommandHandler("publicar",             cmd_publicar))
    app.add_handler(CommandHandler("retirar",              cmd_retirar))
    app.add_handler(CommandHandler("sugerencias",          cmd_sugerencias))

    # Intercambios
    app.add_handler(CommandHandler("intercambios",         cmd_intercambios))
    app.add_handler(CommandHandler("proponer",             cmd_proponer))
    app.add_handler(CommandHandler("aceptar_intercambio",  cmd_aceptar_intercambio))
    app.add_handler(CommandHandler("rechazar_intercambio", cmd_rechazar_intercambio))

    # Subastas
    app.add_handler(CommandHandler("subastas",             cmd_subastas))
    app.add_handler(CommandHandler("crear_subasta",        cmd_crear_subasta))
    app.add_handler(CommandHandler("ofertar",              cmd_ofertar))
    app.add_handler(CommandHandler("cancelar_subasta",     cmd_cancelar_subasta))
    app.add_handler(CommandHandler("mis_subastas",         cmd_mis_subastas))

    # Maestro
    app.add_handler(CommandHandler("buscar",               cmd_buscar))
    app.add_handler(CommandHandler("equipos",              cmd_equipos))

    # Admin
    app.add_handler(CommandHandler("estadisticas",         cmd_estadisticas))

    app.add_error_handler(error_handler)

    print("FiguSwap Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
