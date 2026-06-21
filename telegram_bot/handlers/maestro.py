from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get
from handlers.helpers import fmt_error


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Uso: /buscar numero\nEjemplo: /buscar 10")
        return
    try:
        numero = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ El numero debe ser un entero.")
        return

    token = session.get_token(update.effective_user.id)
    status, data = await api_get(f"/maestro/{numero}", token=token)
    if status == 200:
        jugador = data.get("jugador") or data.get("nombre", "?")
        equipo = data.get("equipo", "?")
        await update.effective_message.reply_text(f"🔎 Figurita #{numero}\nJugador: {jugador}\nEquipo: {equipo}")
    elif status == 404:
        await update.effective_message.reply_text(f"❌ La figurita #{numero} no existe en el maestro.")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


async def cmd_equipos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/maestro/equipos", token=token)
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.effective_message.reply_text("No hay equipos en el maestro.")
        return
    equipos = data if isinstance(data, list) else data.get("equipos", [])
    await update.effective_message.reply_text("🌍 Equipos:\n" + "\n".join(f"  • {e}" for e in equipos))
