from typing import Any
from app.repositories import usuario_repo, publicacion_repo, intercambio_repo, subasta_repo
from app.schemas import EstadoIntercambio


def obtener_estadisticas() -> dict:
    usuarios = usuario_repo.get_all()
    publicaciones = publicacion_repo.get_all()
    intercambios = intercambio_repo.list_exchanges()
    subastas = subasta_repo.get_all()

    estados = {e.value: 0 for e in EstadoIntercambio}
    for i in intercambios:
        e = i.estado.value
        if e in estados:
            estados[e] += 1

    conteo_selecciones: dict[str, int] = {}
    for p in publicaciones:
        eq = p.equipo
        conteo_selecciones[eq] = conteo_selecciones.get(eq, 0) + 1
    filas: list[dict[str, Any]] = [{"seleccion": k, "cantidad": v} for k, v in conteo_selecciones.items()]
    top_selecciones = sorted(filas, key=lambda x: x["cantidad"], reverse=True)[:5]

    return {
        "usuarios": len(usuarios),
        "figuritas_publicadas": len(publicaciones),
        "intercambios_aceptados": estados[EstadoIntercambio.ACEPTADO.value],
        "subastas_activas": len(subastas),
        "intercambios_por_estado": estados,
        "top_selecciones": top_selecciones,
    }
