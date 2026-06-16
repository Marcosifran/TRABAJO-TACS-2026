from datetime import UTC, datetime, timedelta
from typing import Any
import logging

from app.repositories import (
    usuario_repo,
    publicacion_repo,
    intercambio_repo,
    subasta_repo,
    calificacion_repo,
    stats_repo,
)
from app.schemas import EstadoIntercambio

logger = logging.getLogger(__name__)

# Caché persistente en memoria
_stats_cache = {
    "global": {
        "usuarios": 0,
        "figuritas_publicadas": 0,
        "intercambios_aceptados": 0,
        "subastas_activas": 0,
        "intercambios_por_estado": {},
        "top_selecciones": [],
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 300,
        }
    },
    "tendencias": {
        "nuevos_usuarios_24h": 0,
        "intercambios_completados_24h": 0,
        "subastas_finalizadas_24h": 0,
        "figuritas_publicadas_24h": 0,
        "velocidad_promedio_intercambio_horas": 0.0,
        "tasa_exito_intercambios": 0.0,
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 1800,
        }
    },
    "figuritas": {
        "top_10_mas_demandadas": [],
        "top_10_mas_publicadas": [],
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 1800,
        }
    },
    "usuarios": {
        "top_10_mas_activos": [],
        "usuarios_inactivos_7d": 0,
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 1800,
        }
    },
    "mercado": {
        "salud_general": "moderada",
        "volumen_intercambios_7d": 0,
        "volumen_ofertas_subastas_7d": 0,
        "equipos_con_mas_movimiento": [],
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 3600,
        }
    },
    "reputacion": {
        "promedio_global": 0.0,
        "distribucion": {
            "oro": 0,
            "plata": 0,
            "bronce": 0,
            "nuevo": 0,
        },
        "usuarios_top_reputacion": [],
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 1800,
        }
    },
    "performance": {
        "tiempo_promedio_respuesta_horas": 0.0,
        "tiempo_promedio_intercambio_completacion_dias": 0.0,
        "tasa_abandono": 0.0,
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 3600,
        }
    },
    "historico": {
        "periodos": {
            "ultimas_24h": {},
            "ultimos_7d": {},
            "ultimos_30d": {},
            "ultimos_90d": {},
        },
        "timeline": [],
        "_metadata": {
            "ultimo_update": None,
            "frecuencia_segundos": 3600,
        }
    },
}


def _actualizar_metadata(grupo: str, frecuencia_seg: int, error: Exception = None) -> None:
    """Actualiza el _metadata de un grupo de métricas"""
    estado = "error" if error else "ok"
    if error:
        logger.error(f"Error actualizando {grupo}: {error}")

    _stats_cache[grupo]["_metadata"] = {
        "ultimo_update": datetime.now(UTC).isoformat(),
        "frecuencia_segundos": frecuencia_seg,
        "estado": estado,
    }


def _calcular_metricas_basicas() -> dict:
    """Calcula métricas globales básicas"""
    try:
        usuarios = usuario_repo.get_all()
        publicaciones = publicacion_repo.get_all()
        intercambios = intercambio_repo.list_exchanges()
        subastas = subasta_repo.get_all()

        # Contar estados de intercambios
        estados = {e.value: 0 for e in EstadoIntercambio}
        for i in intercambios:
            e = i.estado.value
            if e in estados:
                estados[e] += 1

        # Top selecciones
        conteo_selecciones: dict[str, int] = {}
        for p in publicaciones:
            eq = p.equipo
            conteo_selecciones[eq] = conteo_selecciones.get(eq, 0) + 1

        filas: list[dict[str, Any]] = [{"seleccion": k, "cantidad": v} for k, v in conteo_selecciones.items()]
        top_selecciones = sorted(filas, key=lambda x: x["cantidad"], reverse=True)[:5]

        return {
            "usuarios": len(usuarios),
            "figuritas_publicadas": len(publicaciones),
            "intercambios_aceptados": estados.get(EstadoIntercambio.ACEPTADO.value, 0),
            "subastas_activas": len(subastas),
            "intercambios_por_estado": estados,
            "top_selecciones": top_selecciones,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas básicas: {e}")
        raise


def _calcular_metricas_tendencias() -> dict:
    """Calcula tendencias de los últimos 24h y agregados"""
    try:
        ahora = datetime.now(UTC)
        hace_24h = ahora - timedelta(hours=24)

        intercambios = intercambio_repo.list_exchanges()
        publicaciones = publicacion_repo.get_all()
        subastas = subasta_repo.get_all()

        # Contar intercambios completados en 24h (por ahora, todos los aceptados como proxy)
        intercambios_completados_24h = sum(
            1 for i in intercambios if i.estado.value == EstadoIntercambio.ACEPTADO.value
        )

        # Contar figuritas publicadas en 24h (sin timestamp, contamos todas por ahora)
        figuritas_publicadas_24h = len(publicaciones)

        # Subastas finalizadas en 24h
        subastas_finalizadas_24h = sum(
            1 for s in subastas if s.estado == "finalizada"
        )

        # Nuevos usuarios en 24h (sin timestamp de creación, asumimos todos)
        usuarios = usuario_repo.get_all()
        nuevos_usuarios_24h = len(usuarios)

        # Tasa de éxito
        intercambios_totales = len(intercambios)
        tasa_exito = (intercambios_completados_24h / intercambios_totales * 100) if intercambios_totales > 0 else 0.0

        # Velocidad promedio (placeholder - sin timestamps en datos)
        velocidad_promedio = 24.0  # horas default

        return {
            "nuevos_usuarios_24h": nuevos_usuarios_24h,
            "intercambios_completados_24h": intercambios_completados_24h,
            "subastas_finalizadas_24h": subastas_finalizadas_24h,
            "figuritas_publicadas_24h": figuritas_publicadas_24h,
            "velocidad_promedio_intercambio_horas": velocidad_promedio,
            "tasa_exito_intercambios": round(tasa_exito, 2),
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de tendencias: {e}")
        raise


def _calcular_metricas_figuritas() -> dict:
    """Calcula métricas de figuritas: demanda, popularidad"""
    try:
        publicaciones = publicacion_repo.get_all()
        intercambios = intercambio_repo.list_exchanges()

        # Contar figuritas por equipo
        demanda_por_numero: dict[int, int] = {}
        for i in intercambios:
            num = i.figurita_solicitada
            demanda_por_numero[num] = demanda_por_numero.get(num, 0) + 1

        publicadas_por_numero: dict[int, int] = {}
        figuritas_info: dict[int, dict] = {}
        for p in publicaciones:
            num = p.numero
            publicadas_por_numero[num] = publicadas_por_numero.get(num, 0) + p.cantidad_disponible
            figuritas_info[num] = {"equipo": p.equipo, "jugador": p.jugador}

        # Top 10 más demandadas
        top_demandadas = sorted(
            [
                {
                    "numero": num,
                    "equipo": figuritas_info.get(num, {}).get("equipo", ""),
                    "jugador": figuritas_info.get(num, {}).get("jugador", ""),
                    "demanda": count,
                    "oferta": publicadas_por_numero.get(num, 0),
                    "ratio": count / publicadas_por_numero.get(num, 1) if publicadas_por_numero.get(num, 0) > 0 else 0,
                }
                for num, count in demanda_por_numero.items()
            ],
            key=lambda x: x["demanda"],
            reverse=True,
        )[:10]

        # Top 10 más publicadas
        top_publicadas = sorted(
            [
                {
                    "numero": num,
                    "equipo": figuritas_info.get(num, {}).get("equipo", ""),
                    "jugador": figuritas_info.get(num, {}).get("jugador", ""),
                    "cantidad": count,
                }
                for num, count in publicadas_por_numero.items()
            ],
            key=lambda x: x["cantidad"],
            reverse=True,
        )[:10]

        # Figuritas sin demanda
        sin_demanda = len(set(publicadas_por_numero.keys()) - set(demanda_por_numero.keys()))

        return {
            "top_10_mas_demandadas": top_demandadas,
            "top_10_mas_publicadas": top_publicadas,
            "figuritas_sin_demanda": sin_demanda,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de figuritas: {e}")
        raise


def _calcular_metricas_usuarios() -> dict:
    """Calcula métricas de actividad y reputación de usuarios"""
    try:
        usuarios = usuario_repo.get_all()
        intercambios = intercambio_repo.list_exchanges()
        calificaciones = calificacion_repo.list_all()

        # Contar actividad por usuario
        actividad_por_usuario: dict[int, int] = {}
        for i in intercambios:
            for uid in [i.propuesto_por, i.solicitado_a]:
                actividad_por_usuario[uid] = actividad_por_usuario.get(uid, 0) + 1

        # Reputación por usuario
        reputacion_por_usuario: dict[int, dict] = {}
        for c in calificaciones:
            uid = c["calificado_id"]
            if uid not in reputacion_por_usuario:
                reputacion_por_usuario[uid] = {"puntuaciones": []}
            reputacion_por_usuario[uid]["puntuaciones"].append(c["puntuacion"])

        # Top 10 más activos
        top_activos = sorted(
            [
                {
                    "usuario_id": u["id"],
                    "nombre": u["nombre"],
                    "actividad_puntos": actividad_por_usuario.get(u["id"], 0),
                    "intercambios_completados": sum(1 for i in intercambios if i.estado.value == EstadoIntercambio.ACEPTADO.value and (i.propuesto_por == u["id"] or i.solicitado_a == u["id"])),
                    "reputacion_promedio": sum(reputacion_por_usuario.get(u["id"], {}).get("puntuaciones", [0])) / len(reputacion_por_usuario.get(u["id"], {}).get("puntuaciones", [1])) if reputacion_por_usuario.get(u["id"], {}).get("puntuaciones") else 0.0,
                    "confiabilidad": 0.0,  # placeholder
                    "dias_activo": 0,  # sin timestamp
                }
                for u in usuarios
            ],
            key=lambda x: x["actividad_puntos"],
            reverse=True,
        )[:10]

        # Usuarios inactivos en 7 días (sin timestamps, placeholder)
        usuarios_inactivos_7d = 0

        return {
            "top_10_mas_activos": top_activos,
            "usuarios_inactivos_7d": usuarios_inactivos_7d,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de usuarios: {e}")
        raise


def _calcular_metricas_mercado() -> dict:
    """Calcula salud del mercado y métricas agregadas"""
    try:
        intercambios = intercambio_repo.list_exchanges()
        publicaciones = publicacion_repo.get_all()
        subastas = subasta_repo.get_all()

        # Volumen últimos 7 días
        intercambios_7d = len(intercambios)
        ofertas_subastas_7d = len(subastas)

        # Equipos con más movimiento
        movimiento_por_equipo: dict[str, int] = {}
        for p in publicaciones:
            equipo = p.equipo
            movimiento_por_equipo[equipo] = movimiento_por_equipo.get(equipo, 0) + 1

        equipos_movimiento = sorted(
            [{"equipo": eq, "intercambios": count} for eq, count in movimiento_por_equipo.items()],
            key=lambda x: x["intercambios"],
            reverse=True,
        )[:5]

        # Salud general (score 0-100)
        aceptados = sum(1 for i in intercambios if i.estado.value == EstadoIntercambio.ACEPTADO.value)
        tasa_exito = (aceptados / len(intercambios) * 100) if intercambios else 0
        volumen_score = min((intercambios_7d / 50) * 100, 100)
        salud_score = (tasa_exito + volumen_score) / 2

        if salud_score >= 70:
            salud = "buena"
        elif salud_score >= 40:
            salud = "moderada"
        else:
            salud = "baja"

        return {
            "salud_general": salud,
            "volumen_intercambios_7d": intercambios_7d,
            "volumen_ofertas_subastas_7d": ofertas_subastas_7d,
            "equipos_con_mas_movimiento": equipos_movimiento,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de mercado: {e}")
        raise


def _calcular_metricas_reputacion() -> dict:
    """Calcula estadísticas de reputación global"""
    try:
        calificaciones = calificacion_repo.list_all()
        usuarios = usuario_repo.get_all()

        # Agrupar por usuario calificado
        reputacion_por_usuario: dict[int, dict] = {}
        for c in calificaciones:
            uid = c["calificado_id"]
            if uid not in reputacion_por_usuario:
                reputacion_por_usuario[uid] = []
            reputacion_por_usuario[uid].append(c["puntuacion"])

        # Calcular promedios y niveles
        usuarios_por_nivel = {"oro": 0, "plata": 0, "bronce": 0, "nuevo": 0}
        usuarios_top_reputacion = []

        for uid, puntuaciones in reputacion_por_usuario.items():
            promedio = sum(puntuaciones) / len(puntuaciones)
            usuario = next((u for u in usuarios if u["id"] == uid), None)

            if usuario:
                usuarios_top_reputacion.append({
                    "usuario_id": uid,
                    "nombre": usuario["nombre"],
                    "promedio": round(promedio, 2),
                    "cantidad": len(puntuaciones),
                })

            if promedio >= 4.5:
                usuarios_por_nivel["oro"] += 1
            elif promedio >= 3.5:
                usuarios_por_nivel["plata"] += 1
            elif promedio >= 2.5:
                usuarios_por_nivel["bronce"] += 1
            else:
                usuarios_por_nivel["nuevo"] += 1

        # Usuarios sin calificaciones
        usuarios_sin_calif = len(usuarios) - len(reputacion_por_usuario)
        usuarios_por_nivel["nuevo"] += usuarios_sin_calif

        # Top reputación
        usuarios_top_reputacion = sorted(usuarios_top_reputacion, key=lambda x: x["promedio"], reverse=True)[:10]

        # Promedio global
        promedio_global = sum(sum(vals) / len(vals) for vals in reputacion_por_usuario.values()) / len(reputacion_por_usuario) if reputacion_por_usuario else 0.0

        return {
            "promedio_global": round(promedio_global, 2),
            "distribucion": usuarios_por_nivel,
            "usuarios_top_reputacion": usuarios_top_reputacion,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de reputación: {e}")
        raise


def _calcular_metricas_performance() -> dict:
    """Calcula métricas de rendimiento del sistema"""
    try:
        intercambios = intercambio_repo.list_exchanges()

        # Tasa de abandono (propuestas sin respuesta)
        pendientes = sum(1 for i in intercambios if i.estado.value == EstadoIntercambio.PENDIENTE.value)
        tasa_abandono = (pendientes / len(intercambios) * 100) if intercambios else 0.0

        return {
            "tiempo_promedio_respuesta_horas": 24.0,  # placeholder sin timestamps
            "tiempo_promedio_intercambio_completacion_dias": 7.0,  # placeholder
            "tasa_abandono": round(tasa_abandono, 2),
        }
    except Exception as e:
        logger.error(f"Error calculando métricas de performance: {e}")
        raise


def _calcular_metricas_historico() -> dict:
    """Calcula agregados históricos por período y timeline"""
    try:
        ahora = datetime.utcnow()
        periodos = {
            "ultimas_24h": ahora - timedelta(hours=24),
            "ultimos_7d": ahora - timedelta(days=7),
            "ultimos_30d": ahora - timedelta(days=30),
            "ultimos_90d": ahora - timedelta(days=90),
        }

        # Obtener datos históricos de MongoDB
        datos_historicos = {}
        for nombre_periodo, fecha_inicio in periodos.items():
            snapshots = stats_repo.get_snapshots(fecha_inicio, ahora)
            datos_historicos[nombre_periodo] = _agregar_snapshots(snapshots)

        # Timeline últimos 30 días
        hace_30d = ahora - timedelta(days=30)
        timeline = stats_repo.get_timeline_dias(hace_30d, ahora)

        return {
            "periodos": datos_historicos,
            "timeline": timeline,
        }
    except Exception as e:
        logger.error(f"Error calculando métricas históricas: {e}")
        raise


def _agregar_snapshots(snapshots: list[dict]) -> dict:
    """Agrega snapshots en un período"""
    if not snapshots:
        return {
            "usuarios": 0,
            "figuritas_publicadas": 0,
            "intercambios_aceptados": 0,
            "subastas_activas": 0,
            "tasa_exito": 0.0,
            "velocidad_promedio": 0.0,
        }

    datos = snapshots[0]["datos"] if snapshots else {}
    return {
        "usuarios": datos.get("usuarios_totales", 0),
        "figuritas_publicadas": datos.get("figuritas_publicadas", 0),
        "intercambios_aceptados": datos.get("intercambios_aceptados", 0),
        "subastas_activas": datos.get("subastas_activas", 0),
        "tasa_exito": datos.get("tasa_exito_intercambios", 0.0),
        "velocidad_promedio": datos.get("velocidad_promedio_horas", 0.0),
    }


# === Funciones públicas para actualizar grupos ===

def actualizar_global() -> None:
    """Actualiza métricas globales"""
    try:
        datos = _calcular_metricas_basicas()
        _stats_cache["global"].update(datos)
        _actualizar_metadata("global", 300)
    except Exception as e:
        _actualizar_metadata("global", 300, e)


def actualizar_tendencias() -> None:
    """Actualiza métricas de tendencias"""
    try:
        datos = _calcular_metricas_tendencias()
        _stats_cache["tendencias"].update(datos)
        _actualizar_metadata("tendencias", 1800)
    except Exception as e:
        _actualizar_metadata("tendencias", 1800, e)


def actualizar_figuritas() -> None:
    """Actualiza métricas de figuritas"""
    try:
        datos = _calcular_metricas_figuritas()
        _stats_cache["figuritas"].update(datos)
        _actualizar_metadata("figuritas", 1800)
    except Exception as e:
        _actualizar_metadata("figuritas", 1800, e)


def actualizar_usuarios() -> None:
    """Actualiza métricas de usuarios"""
    try:
        datos = _calcular_metricas_usuarios()
        _stats_cache["usuarios"].update(datos)
        _actualizar_metadata("usuarios", 1800)
    except Exception as e:
        _actualizar_metadata("usuarios", 1800, e)


def actualizar_mercado() -> None:
    """Actualiza métricas de mercado"""
    try:
        datos = _calcular_metricas_mercado()
        _stats_cache["mercado"].update(datos)
        _actualizar_metadata("mercado", 3600)
    except Exception as e:
        _actualizar_metadata("mercado", 3600, e)


def actualizar_reputacion() -> None:
    """Actualiza métricas de reputación"""
    try:
        datos = _calcular_metricas_reputacion()
        _stats_cache["reputacion"].update(datos)
        _actualizar_metadata("reputacion", 1800)
    except Exception as e:
        _actualizar_metadata("reputacion", 1800, e)


def actualizar_performance() -> None:
    """Actualiza métricas de performance"""
    try:
        datos = _calcular_metricas_performance()
        _stats_cache["performance"].update(datos)
        _actualizar_metadata("performance", 3600)
    except Exception as e:
        _actualizar_metadata("performance", 3600, e)


def actualizar_historico() -> None:
    """Actualiza métricas históricas"""
    try:
        datos = _calcular_metricas_historico()
        _stats_cache["historico"]["periodos"] = datos["periodos"]
        _stats_cache["historico"]["timeline"] = datos["timeline"]
        _actualizar_metadata("historico", 3600)
    except Exception as e:
        _actualizar_metadata("historico", 3600, e)


def guardar_snapshot_diario() -> None:
    """Guarda snapshot diario en MongoDB"""
    try:
        datos_snapshot = {
            "usuarios_totales": len(usuario_repo.get_all()),
            "usuarios_nuevos": 0,  # sin timestamp de creación
            "figuritas_publicadas": len(publicacion_repo.get_all()),
            "figuritas_publicadas_hoy": 0,  # sin timestamp
            "intercambios_aceptados": sum(1 for i in intercambio_repo.list_exchanges() if i.estado.value == EstadoIntercambio.ACEPTADO.value),
            "intercambios_rechazados": sum(1 for i in intercambio_repo.list_exchanges() if i.estado.value == EstadoIntercambio.RECHAZADO.value),
            "subastas_activas": len([s for s in subasta_repo.get_all() if s.estado == "activa"]),
            "subastas_finalizadas": sum(1 for s in subasta_repo.get_all() if s.estado == "finalizada"),
            "tasa_exito_intercambios": _stats_cache["tendencias"].get("tasa_exito_intercambios", 0.0),
            "velocidad_promedio_horas": _stats_cache["tendencias"].get("velocidad_promedio_intercambio_horas", 0.0),
        }
        stats_repo.save_daily_snapshot(datos_snapshot)
    except Exception as e:
        logger.error(f"Error guardando snapshot diario: {e}")


# === Funciones públicas para consultar caché ===

def obtener_estadisticas(
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> dict:
    """
    Retorna estadísticas globales.

    Sin filtro: devuelve el caché (actualizado en background por el scheduler).
    Con desde/hasta: consulta datos crudos en MongoDB filtrados por fecha de creación.
    """
    if desde is None and hasta is None:
        return _stats_cache["global"].copy()
    return _calcular_estadisticas_en_periodo(desde, hasta)


def _calcular_estadisticas_en_periodo(
    desde: datetime | None,
    hasta: datetime | None,
) -> dict:
    """Calcula estadísticas filtrando por fecha de creación (usa ObjectId como timestamp)."""
    n_usuarios = usuario_repo.count_en_periodo(desde, hasta)
    publicaciones = publicacion_repo.get_all_en_periodo(desde, hasta)
    intercambios = intercambio_repo.list_exchanges_en_periodo(desde, hasta)
    subastas = subasta_repo.get_all_en_periodo(desde, hasta)

    estados = {e.value: 0 for e in EstadoIntercambio}
    for i in intercambios:
        e = i.estado.value
        if e in estados:
            estados[e] += 1

    conteo_selecciones: dict[str, int] = {}
    for p in publicaciones:
        conteo_selecciones[p.equipo] = conteo_selecciones.get(p.equipo, 0) + 1
    top_selecciones = sorted(
        [{"seleccion": k, "cantidad": v} for k, v in conteo_selecciones.items()],
        key=lambda x: x["cantidad"],
        reverse=True,
    )[:5]

    return {
        "usuarios": n_usuarios,
        "figuritas_publicadas": len(publicaciones),
        "intercambios_aceptados": estados.get(EstadoIntercambio.ACEPTADO.value, 0),
        "subastas_activas": len(subastas),
        "intercambios_por_estado": estados,
        "top_selecciones": top_selecciones,
        "periodo": {
            "desde": desde.date().isoformat() if desde else None,
            "hasta": hasta.date().isoformat() if hasta else None,
        },
        "_metadata": {
            "ultimo_update": datetime.now(UTC).isoformat(),
            "frecuencia_segundos": None,
            "estado": "ok",
        },
    }


def obtener_todas_estadisticas() -> dict:
    """Retorna todas las métricas desde caché"""
    return {k: v.copy() for k, v in _stats_cache.items()}


def obtener_estadisticas_historico(periodo: str = "ultimos_7d") -> dict:
    """Retorna métricas históricas para un período específico"""
    periodos_validos = ["ultimas_24h", "ultimos_7d", "ultimos_30d", "ultimos_90d"]
    if periodo not in periodos_validos:
        periodo = "ultimos_7d"

    historico = _stats_cache["historico"].copy()
    return {
        "periodo": periodo,
        "datos": historico["periodos"].get(periodo, {}),
        "timeline": historico["timeline"],
        "_metadata": historico["_metadata"],
    }
