from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_post
from handlers.helpers import fmt_error

AYUDA = (
    "👋 Bienvenido a FiguSwap Bot!\n\n"
    "🔐 Auth\n"
    "  /login email contraseña\n"
    "  /logout\n"
    "  /registro nombre email contraseña\n\n"
    "📚 Album\n"
    "  /mi_album — mis figuritas\n"
    "  /mi_album_ids — mis figuritas con IDs\n"
    "  /agregar numero cantidad — agrega al album\n"
    "  /eliminar_figurita id\n\n"
    "🔍 Faltantes\n"
    "  /faltantes\n"
    "  /agregar_faltante numero\n\n"
    "📢 Publicaciones\n"
    "  /publicaciones — ver de otros usuarios\n"
    "  /publicaciones_id — con IDs\n"
    "  /mis_publicaciones\n"
    "  /mis_publicaciones_id — con IDs\n"
    "  /publicar numero tipo cantidad\n"
    "    (tipo: directo | subasta)\n"
    "  /retirar id\n"
    "  /sugerencias\n\n"
    "🔄 Intercambios\n"
    "  /intercambios\n"
    "  /proponer usuario_id num_ofrecida num_solicitada\n"
    "  /aceptar_intercambio id\n"
    "  /rechazar_intercambio id\n\n"
    "🏷 Subastas\n"
    "  /subastas\n"
    "  /mis_subastas\n"
    "  /crear_subasta publicacion_id horas\n"
    "  /ofertar subasta_id figurita_id\n"
    "  /ofertas_subasta subasta_id — ofertas recibidas\n"
    "  /responder_oferta subasta_id oferta_id aceptar|rechazar\n"
    "  /cancelar_subasta id\n\n"
    "🔎 Maestro\n"
    "  /buscar numero\n"
    "  /equipos\n\n"
    "👥 Usuarios\n"
    "  /usuarios\n\n"
    "📊 Admin\n"
    "  /estadisticas"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(AYUDA)


async def cmd_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text("Uso: /login email contraseña")
        return
    email, password = context.args[0], context.args[1]
    status, data = await api_post("/auth/login", {"email": email, "password": password})
    if status == 200:
        session.set_session(update.effective_user.id, data["access_token"], data["usuario"])
        u = data["usuario"]
        admin = " (admin)" if u.get("es_admin") else ""
        await update.effective_message.reply_text(f"✅ Bienvenido, {u['nombre']} (ID {u['id']}){admin}!")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session.clear_session(update.effective_user.id)
    await update.effective_message.reply_text("👋 Sesión cerrada.")


async def cmd_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.effective_message.reply_text("Uso: /registro nombre email contraseña")
        return
    nombre, email, password = context.args[0], context.args[1], context.args[2]
    status, data = await api_post("/auth/register", {"nombre": nombre, "email": email, "password": password})
    if status == 201:
        await update.effective_message.reply_text(
            f"✅ Cuenta creada. Ahora iniciá sesión:\n/login {email} {password}"
        )
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
