from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get
from handlers.helpers import require_auth, fmt_error


@require_auth
async def cmd_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/admin/estadisticas", token=token)
    if status == 403:
        await update.effective_message.reply_text("❌ Solo los administradores pueden ver estadísticas.")
        return
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return

    lineas = ["📊 Estadísticas:"]
    for key, val in data.items():
        if isinstance(val, dict):
            lineas.append(f"\n{key}:")
            for k, v in val.items():
                lineas.append(f"  {k}: {v}")
        else:
            lineas.append(f"  {key}: {val}")
    await update.effective_message.reply_text("\n".join(lineas))
