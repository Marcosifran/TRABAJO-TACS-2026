from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post
from handlers.helpers import require_auth, fmt_error


@require_auth
async def cmd_faltantes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/usuarios/faltantes", token=token)
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.effective_message.reply_text("No tenés faltantes registrados. Usá /agregar_faltante numero")
        return
    lineas = ["🔍 Tus faltantes:"]
    for f in data:
        extra = f" — {f['jugador']}" if f.get("jugador") else ""
        equipo = f" ({f['equipo']})" if f.get("equipo") else ""
        lineas.append(f"  #{f['numero_figurita']}{extra}{equipo}  ID: {f['id']}")
    await update.effective_message.reply_text("\n".join(lineas))


@require_auth
async def cmd_agregar_faltante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Uso: /agregar_faltante numero\nEjemplo: /agregar_faltante 42")
        return
    try:
        numero = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ El numero debe ser un entero.")
        return

    token = session.get_token(update.effective_user.id)
    status, data = await api_post("/usuarios/faltantes", {"numero_figurita": numero}, token=token)
    if status == 201:
        await update.effective_message.reply_text(f"✅ Figurita #{numero} marcada como faltante.")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = session.get_usuario(update.effective_user.id)
    if not (usuario and usuario.get("es_admin")):
        await update.effective_message.reply_text("❌ Sin acceso a funcionalidades de admin")
        return
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/admin/usuarios", token=token)
    if status == 403:
        await update.effective_message.reply_text("❌ Sin acceso a funcionalidades de admin")
        return
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.effective_message.reply_text("No hay usuarios registrados.")
        return
    lineas = ["👥 Usuarios:"]
    for u in data:
        admin = " (admin)" if u.get("es_admin") else ""
        lineas.append(f"  ID {u['id']}: {u['nombre']}{admin}")
    await update.effective_message.reply_text("\n".join(lineas))
