from typing import Any
from app.repositories import usuario_repo, publicacion_repo, intercambio_repo, subasta_repo, calificacion_repo
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


def listar_calificaciones() -> list[dict]:
    calificaciones = calificacion_repo.list_all()
    usuarios_por_id = {u["id"]: u["nombre"] for u in usuario_repo.get_all()}
    resultado = []
    for c in calificaciones:
        resultado.append({
            "id": c["id"],
            "intercambio_id": c["intercambio_id"],
            "calificador_id": c["calificador_id"],
            "calificador_nombre": usuarios_por_id.get(c["calificador_id"], f"Usuario {c['calificador_id']}"),
            "calificado_id": c["calificado_id"],
            "calificado_nombre": usuarios_por_id.get(c["calificado_id"], f"Usuario {c['calificado_id']}"),
            "puntuacion": c["puntuacion"],
            "comentario": c.get("comentario"),
        })
    return resultado
