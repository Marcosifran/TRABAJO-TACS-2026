from fastapi import HTTPException
from app.repositories import album_repo, publicacion_repo, usuario_repo
from app.schemas.publicacion_sch import PublicacionCreate

def publicar_figurita(publicacion: PublicacionCreate, usuario_id: int) -> dict:
    """ pone una figurita del album personal en oferta publica para intercambio. Valida que la figurita exista, sea del usuario, no este ya publicaca y la cantidad no supere a la cantidad en album"""
    figurita = album_repo.get_by_id(publicacion.figurita_personal_id)

    if not figurita:
        raise HTTPException(status_code=404, detail="Figurita no encontrada en el álbum del usuario")
    if figurita["usuario_id"] != usuario_id:
        raise HTTPException(status_code=403, detail="La figurita no pertenece al usuario")
    if publicacion_repo.get_by_figurita_personal(publicacion.figurita_personal_id):
        raise HTTPException(status_code=409, detail="La figurita ya está publicada para intercambio")
    if publicacion.cantidad_disponible > figurita["cantidad"]:
        raise HTTPException(status_code=400, detail="La cantidad disponible no puede ser mayor a la cantidad en el álbum")
    
    return publicacion_repo.create(
        publicacion=publicacion,
        usuario_id=usuario_id,
        numero=figurita["numero"],
        equipo=figurita["equipo"],
        jugador=figurita["jugador"],
    )

def listar_publicaciones(
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    tipo_intercambio: str | None,
    excluir_usuario_id: int | None
) -> list[dict]:
    """Retorna las figuritas disponibles poara intercambio aplicando filtros, excluir es para no ver sus propias ofertas"""
    return publicacion_repo.buscar(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        tipo_intercambio=tipo_intercambio,
        usuario_id=excluir_usuario_id,
    )

def retirar_publicacion(publicacion_id: int, usuario_id:int) -> bool | None:
    """ Retira una figurita de la oferta publica"""
    publicacion = publicacion_repo.get_by_id(publicacion_id)

    if publicacion is None:
        return False
    
    if publicacion["usuario_id"] != usuario_id:
        return None
    
    publicacion_repo.delete(publicacion_id)
    return True

def obtener_sugerencias(usuario_id: int) -> list[dict]:
    """ Genera sugerencias automaticas de intercambio para el usuario, desde faltantes del usuario con publicaciones de otros"""
    faltantes = usuario_repo.get_faltantes(usuario_id)

    if not faltantes:
        return []
    
    numeros_faltantes = {f["numero_figurita"] for f in faltantes}

    publicaciones = publicacion_repo.buscar(
        numero=None,
        equipo=None,
        jugador=None,
        usuario_id=usuario_id,
    )

    sugerencias = []
    for pub in publicaciones:
        if pub["numero"] in numeros_faltantes:
            oferente = usuario_repo.get_by_id(pub["usuario_id"])
            sugerencias.append({
                "publicacion": pub,
                "ofrecida_por": oferente["nombre"] if oferente else "Usuario desconocido",
                "cubre_tu_faltante": pub["numero"],
            })

    return sugerencias

def mis_publicaciones(usuario_id: int) -> list[dict]:
    """
    Retorna las publicaciones activas del usuario autenticado.
    """
    return publicacion_repo.get_by_usuario(usuario_id)

