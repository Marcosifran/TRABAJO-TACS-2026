from pydantic import BaseModel, Field
from typing import Any, Optional


class EstadisticaMetadata(BaseModel):
    """Metadata de una métrica: cuándo se actualizó y con qué frecuencia"""
    ultimo_update: Optional[str] = Field(None, description="ISO timestamp de última actualización")
    frecuencia_segundos: int = Field(..., description="Frecuencia de actualización en segundos")
    estado: str = Field(default="ok", description="Estado: ok o error")


class EstadisticasGlobales(BaseModel):
    """Estadísticas globales de uso de la plataforma"""
    usuarios: int
    figuritas_publicadas: int
    intercambios_aceptados: int
    subastas_activas: int
    intercambios_por_estado: dict[str, int]
    top_selecciones: list[dict[str, Any]]
    _metadata: EstadisticaMetadata


class EstadisticasTendencias(BaseModel):
    """Tendencias y análisis de actividad"""
    nuevos_usuarios_24h: int
    intercambios_completados_24h: int
    subastas_finalizadas_24h: int
    figuritas_publicadas_24h: int
    velocidad_promedio_intercambio_horas: float
    tasa_exito_intercambios: float
    _metadata: EstadisticaMetadata


class FiguritaEstadistica(BaseModel):
    """Información estadística de una figurita"""
    numero: int
    equipo: str
    jugador: str
    demanda: int = 0
    oferta: int = 0
    ratio: float = 0.0
    cantidad: int = 0


class EstadisticasFiguritas(BaseModel):
    """Estadísticas de figuritas: demanda y popularidad"""
    top_10_mas_demandadas: list[FiguritaEstadistica]
    top_10_mas_publicadas: list[FiguritaEstadistica]
    figuritas_sin_demanda: int = 0
    _metadata: EstadisticaMetadata


class UsuarioActividad(BaseModel):
    """Información de actividad de un usuario"""
    usuario_id: int
    nombre: str
    actividad_puntos: int
    intercambios_completados: int
    reputacion_promedio: float
    confiabilidad: float
    dias_activo: int


class EstadisticasUsuarios(BaseModel):
    """Estadísticas de usuarios: actividad y comportamiento"""
    top_10_mas_activos: list[UsuarioActividad]
    usuarios_inactivos_7d: int
    _metadata: EstadisticaMetadata


class EquipoMovimiento(BaseModel):
    """Estadísticas de movimiento por equipo"""
    equipo: str
    intercambios: int


class EstadisticasMercado(BaseModel):
    """Estadísticas de salud y movimiento del mercado"""
    salud_general: str = Field(..., description="Estado: buena, moderada, baja")
    volumen_intercambios_7d: int
    volumen_ofertas_subastas_7d: int
    equipos_con_mas_movimiento: list[EquipoMovimiento]
    _metadata: EstadisticaMetadata


class DistribucionReputacion(BaseModel):
    """Distribución de usuarios por nivel de reputación"""
    oro: int = Field(default=0, description=">= 4.5 estrellas")
    plata: int = Field(default=0, description="3.5-4.5 estrellas")
    bronce: int = Field(default=0, description="2.5-3.5 estrellas")
    nuevo: int = Field(default=0, description="< 2.5 estrellas o sin calificaciones")


class UsuarioReputacion(BaseModel):
    """Usuario con información de reputación"""
    usuario_id: int
    nombre: str
    promedio: float
    cantidad: int


class EstadisticasReputacion(BaseModel):
    """Estadísticas de reputación global"""
    promedio_global: float
    distribucion: DistribucionReputacion
    usuarios_top_reputacion: list[UsuarioReputacion]
    _metadata: EstadisticaMetadata


class EstadisticasPerformance(BaseModel):
    """Métricas de performance del sistema"""
    tiempo_promedio_respuesta_horas: float
    tiempo_promedio_intercambio_completacion_dias: float
    tasa_abandono: float = Field(..., description="Porcentaje de propuestas sin respuesta")
    _metadata: EstadisticaMetadata


class DatosHistoricosPeriodo(BaseModel):
    """Datos agregados para un período específico"""
    usuarios: int
    figuritas_publicadas: int
    intercambios_aceptados: int
    subastas_activas: int
    tasa_exito: float
    velocidad_promedio: float


class DiaDatos(BaseModel):
    """Datos de un día en la timeline"""
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    usuarios: int
    figuritas_publicadas: int
    intercambios_aceptados: int
    subastas_activas: int


class EstadisticasHistorico(BaseModel):
    """Estadísticas históricas por período"""
    periodo: str = Field(..., description="Período: ultimas_24h, ultimos_7d, ultimos_30d, ultimos_90d")
    datos: DatosHistoricosPeriodo
    timeline: list[DiaDatos]
    _metadata: EstadisticaMetadata


class TodasEstadisticas(BaseModel):
    """Todas las estadísticas disponibles"""
    global_: EstadisticasGlobales = Field(alias="global")
    tendencias: EstadisticasTendencias
    figuritas: EstadisticasFiguritas
    usuarios: EstadisticasUsuarios
    mercado: EstadisticasMercado
    reputacion: EstadisticasReputacion
    performance: EstadisticasPerformance
    historico: EstadisticasHistorico

    class Config:
        populate_by_name = True
