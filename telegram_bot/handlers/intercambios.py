from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post, api_patch
from handlers.helpers import require_auth, fmt_error


def _fmt_intercambio(i: dict) -> str:
    estado = i["estado"].upper()
    return (
        f"  ID: {i['id']}\n"
        f"  De usuario {i['propuesto_por']} → a usuario {i['solicitado_a']}\n"
        f"  Ofrece: {i['figuritas_ofrecidas']}  pide: #{i['figurita_solicitada']}\n"
        f"  Estado: {estado}"
    )


@require_auth
async def cmd_intercambios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/intercambios/", token=token)
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.message.reply_text("No tenés intercambios. Usá /proponer para iniciar uno.")
        return
    lineas = ["🔄 Tus intercambios:"]
    for i in data:
        lineas.append(_fmt_intercambio(i))
    await update.message.reply_text("\n".join(lineas))


@require_auth
async def cmd_proponer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso: /proponer usuario_id num_ofrecida num_solicitada\n"
            "Ejemplo: /proponer 2 10 42\n\n"
            "Para ofrecer varias: /proponer 2 10,15,20 42\n"
            "Encontrá los usuarios con /usuarios"
        )
        return
    try:
        solicitado_a = int(context.args[0])
        ofrecidas = [int(n) for n in context.args[1].split(",")]
        solicitada = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Los números deben ser enteros. Las ofrecidas se separan con coma (sin espacios).")
        return

    token = session.get_token(update.effective_user.id)
    body = {
        "figuritas_ofrecidas_numero": ofrecidas,
        "figurita_solicitada_numero": solicitada,
        "solicitado_a_id": solicitado_a,
    }
    status, data = await api_post("/intercambios/", body, token=token)
    if status == 201:
        await update.message.reply_text(
            f"✅ Intercambio propuesto.\nID: {data['id']}"
        )
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_aceptar_intercambio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /aceptar_intercambio id")
        return
    intercambio_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_patch(
        f"/intercambios/{intercambio_id}/estado",
        {"estado": "aceptado"},
        token=token,
    )
    if status == 200:
        await update.message.reply_text("✅ Intercambio aceptado.")
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_rechazar_intercambio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /rechazar_intercambio id")
        return
    intercambio_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_patch(
        f"/intercambios/{intercambio_id}/estado",
        {"estado": "rechazado"},
        token=token,
    )
    if status == 200:
        await update.message.reply_text("✅ Intercambio rechazado.")
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
