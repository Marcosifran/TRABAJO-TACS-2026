from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post, api_delete
from handlers.helpers import require_auth, fmt_error

_TIPO_MAP = {
    "directo": "intercambio_directo",
    "intercambio_directo": "intercambio_directo",
    "subasta": "subasta",
}


def _fmt_publicacion(p: dict) -> str:
    return (
        f"  #{p['numero']} {p['jugador']} ({p['equipo']}) x{p.get('cantidad_disponible', '?')}\n"
        f"  Tipo: {p['tipo_intercambio']}  ID: {p['id']}"
    )


@require_auth
async def cmd_publicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/publicaciones/", token=token, params={"incluir_propias": "false"})
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    items = data.get("items", data) if isinstance(data, dict) else data
    if not items:
        await update.message.reply_text("No hay publicaciones disponibles.")
        return
    lineas = ["📢 Publicaciones disponibles:"]
    for p in items[:15]:
        lineas.append(_fmt_publicacion(p))
    await update.message.reply_text("\n".join(lineas))


@require_auth
async def cmd_mis_publicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/usuarios/publicaciones", token=token)
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.message.reply_text("No tenés publicaciones. Usá /publicar figurita_id tipo cantidad")
        return
    lineas = ["📢 Mis publicaciones:"]
    for p in data:
        lineas.append(_fmt_publicacion(p))
    await update.message.reply_text("\n".join(lineas))


@require_auth
async def cmd_publicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso: /publicar figurita_id tipo cantidad\n"
            "tipo: directo | subasta\n"
            "Ejemplo: /publicar abc123 directo 2\n\n"
            "Encontrá el figurita_id en /mi_album"
        )
        return
    figurita_id, tipo_raw = context.args[0], context.args[1]
    try:
        cantidad = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ cantidad debe ser un entero.")
        return

    tipo = _TIPO_MAP.get(tipo_raw.lower())
    if not tipo:
        await update.message.reply_text("❌ tipo debe ser 'directo' o 'subasta'.")
        return

    token = session.get_token(update.effective_user.id)
    body = {
        "figurita_personal_id": figurita_id,
        "tipo": tipo,
        "cantidad_disponible": cantidad,
    }
    status, data = await api_post("/publicaciones/", body, token=token)
    if status == 201:
        await update.message.reply_text(
            f"✅ Publicación creada.\nID: {data['id']}"
        )
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_retirar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /retirar id\n(el ID lo ves en /mis_publicaciones)")
        return
    pub_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_delete(f"/publicaciones/{pub_id}", token=token)
    if status == 204:
        await update.message.reply_text("✅ Publicación retirada.")
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_sugerencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/publicaciones/sugerencias", token=token)
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.message.reply_text("No hay sugerencias para vos por ahora.")
        return
    lineas = ["💡 Sugerencias de intercambio:"]
    for s in data[:10]:
        pub = s["publicacion"]
        lineas.append(
            f"  #{pub['numero']} {pub['jugador']} ({pub['equipo']})\n"
            f"  Ofrecida por: {s['ofrecida_por']}  cubre tu faltante #{s['cubre_tu_faltante']}\n"
            f"  Pub ID: {pub['id']}"
        )
    await update.message.reply_text("\n".join(lineas))
