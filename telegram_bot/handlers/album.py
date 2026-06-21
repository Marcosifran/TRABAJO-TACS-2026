from telegram import Update
from telegram.ext import ContextTypes
import session
from api_client import api_get, api_post, api_delete
from handlers.helpers import require_auth, fmt_error
from handlers.banderas import bandera


async def _mostrar_album(update: Update, *, con_ids: bool):
    token = session.get_token(update.effective_user.id)
    status, data = await api_get("/album/", token=token)
    if status != 200:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
        return
    items = data.get("items", data) if isinstance(data, dict) else data
    if not items:
        await update.message.reply_text("Tu album está vacío. Usá /agregar numero cantidad")
        return

    # Mapa figurita_personal_id -> tipo de publicación, para distinguir
    # intercambio directo (🔄) de subasta (📣).
    st_pub, pubs = await api_get("/usuarios/publicaciones", token=token)
    tipos_por_figurita = (
        {p["figurita_personal_id"]: p["tipo_intercambio"] for p in pubs}
        if st_pub == 200 and isinstance(pubs, list)
        else {}
    )

    # Agrupar por equipo (país), ordenado alfabéticamente
    por_equipo: dict[str, list] = {}
    for f in items:
        por_equipo.setdefault(f["equipo"], []).append(f)

    lineas = ["📚 Tu album:"]
    for equipo in sorted(por_equipo):
        flag = bandera(equipo)
        encabezado = f"{flag} {equipo}".strip()
        lineas.append(f"\n{encabezado}")
        for f in sorted(por_equipo[equipo], key=lambda x: x["numero"]):
            marcador = ""
            if f.get("en_intercambio"):
                tipo = tipos_por_figurita.get(f["id"])
                marcador = " 📣" if tipo == "subasta" else " 🔄"
            linea = f"  #{f['numero']} {f['jugador']} x{f['cantidad']}{marcador}"
            if con_ids:
                linea += f"\n  ID: {f['id']}"
            lineas.append(linea)
    await update.message.reply_text("\n".join(lineas))


@require_auth
async def cmd_mi_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_album(update, con_ids=False)


@require_auth
async def cmd_mi_album_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mostrar_album(update, con_ids=True)


@require_auth
async def cmd_agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /agregar numero cantidad\nEjemplo: /agregar 10 2")
        return
    try:
        numero = int(context.args[0])
        cantidad = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ numero y cantidad deben ser enteros.")
        return

    token = session.get_token(update.effective_user.id)

    # Buscar datos del jugador en el maestro
    st_m, maestro = await api_get(f"/maestro/{numero}", token=token)
    if st_m != 200:
        await update.message.reply_text(
            f"❌ No se encontró la figurita #{numero} en el maestro.\n"
            "Verificá el número e intentá de nuevo."
        )
        return

    body = {
        "numero": numero,
        "equipo": maestro.get("equipo", "Desconocido"),
        "jugador": maestro.get("jugador", maestro.get("nombre", "Desconocido")),
        "cantidad": cantidad,
    }
    status, data = await api_post("/album/", body, token=token)
    if status == 201:
        await update.message.reply_text(
            f"✅ Agregada: #{numero} {body['jugador']} ({body['equipo']}) x{cantidad}\n"
            f"ID: {data['id']}"
        )
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")


@require_auth
async def cmd_eliminar_figurita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /eliminar_figurita id\n(el ID lo ves en /mi_album)")
        return
    figurita_id = context.args[0]
    token = session.get_token(update.effective_user.id)
    status, data = await api_delete(f"/album/{figurita_id}", token=token)
    if status == 204:
        await update.message.reply_text("✅ Figurita eliminada del album.")
    else:
        await update.message.reply_text(f"❌ {fmt_error(data)}")
