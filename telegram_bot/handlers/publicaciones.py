from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post, api_delete
from handlers.helpers import require_auth, fmt_error
from handlers.banderas import bandera

_TIPO_MAP = {
    "directo": "intercambio_directo",
    "intercambio_directo": "intercambio_directo",
    "subasta": "subasta",
}


def _tipo_emoji(tipo: str) -> str:
    """📣 para subasta, 🔄 para intercambio directo."""
    return "📣" if tipo == "subasta" else "🔄"


def _render_publicaciones(items: list[dict], header: str, *, con_ids: bool) -> str:
    """Agrupa publicaciones por país (con bandera) y muestra el tipo como emoji."""
    por_equipo: dict[str, list] = {}
    for p in items:
        por_equipo.setdefault(p["equipo"], []).append(p)

    lineas = [header]
    for equipo in sorted(por_equipo):
        flag = bandera(equipo)
        encabezado = f"{flag} {equipo}".strip()
        lineas.append(f"\n{encabezado}")
        for p in sorted(por_equipo[equipo], key=lambda x: x["numero"]):
            emoji = _tipo_emoji(p["tipo_intercambio"])
            linea = f"  #{p['numero']} {p['jugador']} x{p.get('cantidad_disponible', '?')} {emoji}"
            if con_ids:
                linea += f"\n  ID: {p['id']}"
            lineas.append(linea)
    return "\n".join(lineas)


async def _mostrar_publicaciones(update: Update, *, con_ids: bool):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/publicaciones/", token=token, params={"incluir_propias": "false"})
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    items = data.get("items", data) if isinstance(data, dict) else data
    if not items:
        await update.message.reply_text("No hay publicaciones disponibles.")
        return
    await update.message.reply_text(
        _render_publicaciones(items[:15], "📢 Publicaciones disponibles:", con_ids=con_ids)
    )


async def _mostrar_mis_publicaciones(update: Update, *, con_ids: bool):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/usuarios/publicaciones", token=token)
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.message.reply_text("No tenés publicaciones. Usá /publicar figurita_id tipo cantidad")
        return
    await update.message.reply_text(
        _render_publicaciones(data, "📢 Mis publicaciones:", con_ids=con_ids)
    )


@require_auth
async def cmd_publicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_publicaciones(update, con_ids=False)


@require_auth
async def cmd_publicaciones_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_publicaciones(update, con_ids=True)


@require_auth
async def cmd_mis_publicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_mis_publicaciones(update, con_ids=False)


@require_auth
async def cmd_mis_publicaciones_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_mis_publicaciones(update, con_ids=True)


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
