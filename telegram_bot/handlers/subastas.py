import datetime
from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post, api_patch, api_delete
from handlers.helpers import require_auth, fmt_error


def _fmt_subasta(s: dict) -> str:
    jugador = s.get("figurita_jugador", "?")
    equipo = s.get("figurita_equipo", "?")
    numero = s.get("figurita_numero", "?")
    fin = s.get("fin", "?")
    if isinstance(fin, str) and "T" in fin:
        fin = fin.replace("T", " ")[:16]
    return (
        f"  ID: {s['id']}\n"
        f"  Figurita: #{numero} {jugador} ({equipo})\n"
        f"  Estado: {s['estado']}  Finaliza: {fin}"
    )


@require_auth
async def cmd_subastas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/subastas/", token=token)
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    items = data.get("items", data) if isinstance(data, dict) else data
    activas = [s for s in items if s.get("estado") == "activa"]
    if not activas:
        await update.effective_message.reply_text("No hay subastas activas en este momento.")
        return
    lineas = ["🏷 Subastas activas:"]
    for s in activas[:10]:
        lineas.append(_fmt_subasta(s))
    await update.effective_message.reply_text("\n".join(lineas))


@require_auth
async def cmd_crear_subasta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Uso: /crear_subasta publicacion_id horas\n"
            "Ejemplo: /crear_subasta abc123 24\n\n"
            "Encontrá la publicacion_id en /mis_publicaciones"
        )
        return
    publicacion_id = context.args[0]
    try:
        horas = int(context.args[1])
        if horas < 1:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("❌ horas debe ser un entero positivo.")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    fin = now + datetime.timedelta(hours=horas)

    token = session.get_token(update.effective_user.id)
    body = {
        "figurita_id": publicacion_id,
        "inicio": now.isoformat(),
        "fin": fin.isoformat(),
    }
    status, data = await api_post("/subastas/", body, token=token)
    if status == 201:
        await update.effective_message.reply_text(
            f"✅ Subasta creada por {horas} hora(s).\nID: {data['id']}"
        )
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_ofertar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Uso: /ofertar subasta_id figurita_id [figurita_id2 ...]\n"
            "Ejemplo: /ofertar abc123 xyz456\n\n"
            "Encontrá los IDs en /mi_album y /subastas"
        )
        return
    subasta_id = context.args[0]
    figuritas_ofrecidas = list(context.args[1:])
    token = session.get_token(update.effective_user.id)
    status, data = await api_post(
        f"/subastas/{subasta_id}/ofertas",
        {"figuritas_ofrecidas": figuritas_ofrecidas},
        token=token,
    )
    if status == 201:
        await update.effective_message.reply_text(f"✅ Oferta enviada.\nID oferta: {data['id']}")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_cancelar_subasta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Uso: /cancelar_subasta id")
        return
    subasta_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_delete(f"/subastas/{subasta_id}", token=token)
    if status == 204:
        await update.effective_message.reply_text("✅ Subasta cancelada.")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_mis_subastas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/usuarios/subastas", token=token)
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    if not data:
        await update.effective_message.reply_text("No tenés subastas. Usá /crear_subasta para crear una.")
        return
    lineas = ["🏷 Mis subastas:"]
    for s in data:
        lineas.append(_fmt_subasta(s))
    await update.effective_message.reply_text("\n".join(lineas))


@require_auth
async def cmd_ofertas_subasta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "Uso: /ofertas_subasta subasta_id\n"
            "Ejemplo: /ofertas_subasta abc123\n\n"
            "Encontrá el ID en /mis_subastas"
        )
        return
    subasta_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_get(f"/subastas/{subasta_id}/ofertas", token=token)
    if status != 200:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
        return
    items = data.get("items", data) if isinstance(data, dict) else data
    if not items:
        await update.effective_message.reply_text("Esta subasta no tiene ofertas todavía.")
        return
    lineas = [f"📋 Ofertas para subasta {subasta_id}:"]
    for o in items:
        detalle = o.get("ofrecidas_detalle", [])
        if detalle:
            figuritas = ", ".join(f"#{f['numero']} {f['jugador']} ({f['equipo']})" for f in detalle)
        else:
            figuritas = ", ".join(o.get("ofrecidas", [])) or "—"
        lineas.append(
            f"\n  ID oferta: {o['id']}\n"
            f"  Oferente: usuario {o.get('usuario_id', '?')}\n"
            f"  Figuritas ofrecidas: {figuritas}"
        )
    lineas.append("\nUsá /responder_oferta para aceptar o rechazar.")
    await update.effective_message.reply_text("\n".join(lineas))


@require_auth
async def cmd_responder_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.effective_message.reply_text(
            "Uso: /responder_oferta subasta_id oferta_id aceptar|rechazar\n"
            "Ejemplo: /responder_oferta abc123 xyz456 aceptar\n\n"
            "Encontrá los IDs en /ofertas_subasta"
        )
        return
    subasta_id = context.args[0]
    oferta_id = context.args[1]
    decision = context.args[2].lower()
    if decision not in ("aceptar", "rechazar"):
        await update.effective_message.reply_text("❌ La decisión debe ser 'aceptar' o 'rechazar'.")
        return
    estado = "aceptada" if decision == "aceptar" else "rechazada"
    token = session.get_token(update.effective_user.id)
    status, data = await api_patch(
        f"/subastas/{subasta_id}/ofertas/{oferta_id}",
        {"estado": estado},
        token=token,
    )
    if status in (200, 204):
        if decision == "aceptar":
            await update.effective_message.reply_text("✅ Oferta aceptada. ¡Intercambio realizado!")
        else:
            await update.effective_message.reply_text("✅ Oferta rechazada.")
    else:
        await update.effective_message.reply_text(f"❌ {fmt_error(data)}")
