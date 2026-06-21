from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import session


def require_auth(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not session.is_logged_in(update.effective_user.id):
            await update.effective_message.reply_text("❌ No estás logueado. Usá /login email contraseña")
            return
        return await func(update, context)
    return wrapper


def fmt_error(data: dict) -> str:
    detail = data.get("detail", "Error inesperado")
    if isinstance(detail, list):
        return "; ".join(e.get("msg", str(e)) for e in detail)
    return str(detail)


def paginate_text(items: list[str], header: str, empty_msg: str) -> str:
    if not items:
        return empty_msg
    return header + "\n" + "\n".join(items)
