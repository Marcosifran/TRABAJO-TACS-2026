from app.repositories import usuario_repo, publicacion_repo, intercambio_repo, subasta_repo
from app.schemas.intercambio_sch import EstadoIntercambio

def obtener_estadisticas() -> dict:
    usuarios      = usuario_repo.get_all()
    publicaciones = publicacion_repo.get_all()
    intercambios  = intercambio_repo.list_exchanges()
    subastas      = subasta_repo.get_all()

    estados = {e.value: 0 for e in EstadoIntercambio}
    for i in intercambios:
        e = i.get("estado", "pendiente")
        if e in estados:
            estados[e] += 1

    conteo_selecciones: dict[str, int] = {}
    for p in publicaciones:
        eq = p.get("equipo", "Desconocido")
        conteo_selecciones[eq] = conteo_selecciones.get(eq, 0) + 1
    top_selecciones = sorted(
        [{"seleccion": k, "cantidad": v} for k, v in conteo_selecciones.items()],
        key=lambda x: x["cantidad"],
        reverse=True,
    )[:5]

    return {
        "usuarios":               len(usuarios),
        "figuritas_publicadas":   len(publicaciones),
        "intercambios_aceptados": estados["aceptado"],
        "subastas_activas":       len(subastas),
        "intercambios_por_estado": estados,
        "top_selecciones":        top_selecciones,
    }
