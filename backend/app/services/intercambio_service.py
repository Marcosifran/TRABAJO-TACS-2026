from fastapi import HTTPException

from app.repositories import album_repo, publicacion_repo, intercambio_repo, usuario_repo
from app.schemas.intercambio_sch import IntercambioCreate, IntercambioDecision


def validar_figuritas_ofrecidas(intercambio: IntercambioCreate) -> None:
    """Valida que la lista de figuritas ofrecidas no esté vacía ni tenga repetidos."""
    if not intercambio.figuritas_ofrecidas_numero:
        raise HTTPException(status_code=400, detail="Debés ofrecer al menos una figurita")

    if len(intercambio.figuritas_ofrecidas_numero) != len(set(intercambio.figuritas_ofrecidas_numero)):
        raise HTTPException(status_code=400, detail="No podés repetir figuritas en la oferta")


def validar_numeros_distintos(intercambio: IntercambioCreate) -> None:
    """Valida que la figurita solicitada no esté incluida entre las ofrecidas."""
    if intercambio.figurita_solicitada_numero in intercambio.figuritas_ofrecidas_numero:
        raise HTTPException(
            status_code=400,
            detail="La figurita solicitada no puede estar incluida entre las ofrecidas"
        )


def validar_usuario_destino(intercambio: IntercambioCreate, usuario_id: int) -> None:
    """Valida que el usuario no se proponga un intercambio a sí mismo y que exista."""
    if intercambio.solicitado_a_id == usuario_id:
        raise HTTPException(
            status_code=400,
            detail="No podés proponerte un intercambio a vos mismo"
        )

    if not usuario_repo.get_by_id(intercambio.solicitado_a_id):
        raise HTTPException(
            status_code=404,
            detail="El usuario destinatario no existe"
        )


def obtener_publicaciones_para_intercambio(
    intercambio: IntercambioCreate,
    usuario_id: int,
) -> tuple[list[dict], dict]:
    """
    Busca en publicacion_repo las publicaciones involucradas en el intercambio.
    Solo considera publicaciones de tipo intercambio_directo.

    Valida que:
    - El proponente tenga publicadas todas las figuritas que ofrece.
    - El receptor tenga publicada la figurita solicitada.
    - Todas sean de tipo intercambio_directo.

    Returns:
        Tupla (publicaciones_ofrecidas, publicacion_solicitada)
    """
    todas_publicaciones = publicacion_repo.get_all()

    # Buscamos en el álbum del proponente los números ofrecidos
    album_proponente = album_repo.get_by_usuario(usuario_id)
    numeros_en_album = {f["numero"] for f in album_proponente if f["cantidad"] > 0}
    
    numeros_faltantes = [
        n for n in intercambio.figuritas_ofrecidas_numero
        if n not in numeros_en_album
    ]
    
    if numeros_faltantes:
        raise HTTPException(
            status_code=404,
            detail="No tenés en tu álbum todas las figuritas que ofrecés"
        )
    
    # NUEVO: Validar que no estén publicadas como SUBASTA
    for numero in intercambio.figuritas_ofrecidas_numero:
        if any(p["numero"] == numero and p["usuario_id"] == usuario_id and p["tipo_intercambio"] == "subasta" for p in todas_publicaciones):
            raise HTTPException(
                status_code=404,
                detail=f"La figurita {numero} está publicada como subasta"
            )

    # Mantenemos la lógica de que la solicitada SÍ debe estar publicada
    publicaciones_ofrecidas = [] 

    # Buscamos la publicación del receptor con el número solicitado
    publicacion_solicitada = next(
        (
            p for p in todas_publicaciones
            if p["numero"] == intercambio.figurita_solicitada_numero
            and p["usuario_id"] == intercambio.solicitado_a_id
            and p["tipo_intercambio"] == "intercambio_directo"
        ),
        None,
    )

    if not publicacion_solicitada:
        raise HTTPException(
            status_code=404,
            detail="El usuario destino no tiene publicada para intercambio directo la figurita solicitada"
        )

    return publicaciones_ofrecidas, publicacion_solicitada


def validar_cantidad_disponible(
    publicaciones_ofrecidas: list[dict],
    publicacion_solicitada: dict,
) -> None:
    """Valida que todas las publicaciones involucradas tengan cantidad disponible."""
    if any(p["cantidad_disponible"] < 1 for p in publicaciones_ofrecidas):
        raise HTTPException(
            status_code=400,
            detail="Alguna figurita ofrecida no tiene stock disponible"
        )

    if publicacion_solicitada["cantidad_disponible"] < 1:
        raise HTTPException(
            status_code=400,
            detail="La figurita solicitada no tiene stock disponible"
        )


def validar_intercambio(
    intercambio: IntercambioCreate,
    usuario_id: int,
) -> tuple[list[dict], dict]:
    """
    Ejecuta todas las validaciones de negocio para un intercambio propuesto.

    Reglas:
    - La lista de figuritas ofrecidas no puede estar vacía ni tener repetidos.
    - La figurita solicitada no puede estar entre las ofrecidas.
    - No se puede proponer a uno mismo ni a un usuario inexistente.
    - Todas las figuritas deben estar publicadas para intercambio directo.
    - Todas deben tener cantidad disponible.

    Returns:
        Tupla (publicaciones_ofrecidas, publicacion_solicitada)
    """
    validar_figuritas_ofrecidas(intercambio)
    validar_numeros_distintos(intercambio)
    validar_usuario_destino(intercambio, usuario_id)
    publicaciones_ofrecidas, publicacion_solicitada = obtener_publicaciones_para_intercambio(
        intercambio, usuario_id
    )
    validar_cantidad_disponible(publicaciones_ofrecidas, publicacion_solicitada)
    return publicaciones_ofrecidas, publicacion_solicitada


def realizar_intercambio_aceptado(intercambio: dict) -> None:
    """
    Realiza el intercambio efectivo de figuritas entre los usuarios.
    Actualiza tanto el álbum como las publicaciones activas para reflejar el cambio de stock.
    """
    from app.schemas.album_sch import FiguritaAlbumCreate

    # 1. Procesar figuritas ofrecidas por el proponente -> entregadas al solicitado_a
    for numero in intercambio["figuritas_ofrecidas"]:
        # Restar del álbum del proponente
        fig_prop = album_repo.get_por_numero_y_usuario(numero, intercambio["propuesto_por"])
        if fig_prop:
            equipo, jugador = fig_prop["equipo"], fig_prop["jugador"]
            fig_prop["cantidad"] -= 1
            if fig_prop["cantidad"] <= 0:
                album_repo.delete(fig_prop["id"])
        else:
            equipo, jugador = "Desconocido", "Desconocido"

        # Restar de publicaciones del proponente (si existía una para este número)
        pub_prop = next((p for p in publicacion_repo.get_all() 
                        if p["numero"] == numero and p["usuario_id"] == intercambio["propuesto_por"]), None)
        if pub_prop:
            pub_prop["cantidad_disponible"] -= 1
            if pub_prop["cantidad_disponible"] <= 0:
                publicacion_repo.delete(pub_prop["id"])

        # Sumar al álbum del receptor (solicitado_a)
        fig_rec = album_repo.get_por_numero_y_usuario(numero, intercambio["solicitado_a"])
        if fig_rec:
            fig_rec["cantidad"] += 1
        else:
            album_repo.create(
                FiguritaAlbumCreate(numero=numero, equipo=equipo, jugador=jugador, cantidad=1),
                usuario_id=intercambio["solicitado_a"]
            )
        
        # Remover de faltantes del receptor
        usuario_repo.remove_faltante(intercambio["solicitado_a"], numero)

    # 2. Procesar figurita solicitada al receptor -> entregada al proponente
    num_solicitado = intercambio["figurita_solicitada"]
    
    # Restar del álbum del receptor (solicitado_a)
    fig_sol = album_repo.get_por_numero_y_usuario(num_solicitado, intercambio["solicitado_a"])
    if fig_sol:
        equipo_sol, jugador_sol = fig_sol["equipo"], fig_sol["jugador"]
        fig_sol["cantidad"] -= 1
        if fig_sol["cantidad"] <= 0:
            album_repo.delete(fig_sol["id"])
    else:
        equipo_sol, jugador_sol = "Desconocido", "Desconocido"

    # Restar de publicaciones del receptor
    pub_sol = next((p for p in publicacion_repo.get_all() 
                   if p["numero"] == num_solicitado and p["usuario_id"] == intercambio["solicitado_a"]), None)
    if pub_sol:
        pub_sol["cantidad_disponible"] -= 1
        if pub_sol["cantidad_disponible"] <= 0:
            publicacion_repo.delete(pub_sol["id"])

    # Sumar al álbum del proponente
    fig_prop_rec = album_repo.get_por_numero_y_usuario(num_solicitado, intercambio["propuesto_por"])
    if fig_prop_rec:
        fig_prop_rec["cantidad"] += 1
    else:
        album_repo.create(
            FiguritaAlbumCreate(numero=num_solicitado, equipo=equipo_sol, jugador=jugador_sol, cantidad=1),
            usuario_id=intercambio["propuesto_por"]
        )

    # Remover de faltantes del proponente
    usuario_repo.remove_faltante(intercambio["propuesto_por"], num_solicitado)


def responder_intercambio(
    intercambio_id: int,
    decision: IntercambioDecision,
    usuario_id: int,
) -> dict:
    """
    Permite al receptor de un intercambio aceptarlo o rechazarlo.

    Valida que:
    - El intercambio exista.
    - El usuario sea el receptor.
    - El intercambio esté pendiente.

    Returns:
        El intercambio actualizado con el nuevo estado.
    """
    intercambio = intercambio_repo.buscar_intercambio_por_id(intercambio_id)

    if not intercambio:
        raise HTTPException(status_code=404, detail="Intercambio no encontrado")

    if intercambio["solicitado_a"] != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el usuario receptor puede responder este intercambio"
        )

    if intercambio["estado"] != "pendiente":
        raise HTTPException(status_code=400, detail="El intercambio ya fue respondido")

    if decision.estado.value == "aceptado":
        realizar_intercambio_aceptado(intercambio)

    intercambio_actualizado = intercambio_repo.responder_intercambio(
        intercambio_id,
        decision.estado.value,
    )

    if not intercambio_actualizado:
        raise HTTPException(
            status_code=404,
            detail="Intercambio no encontrado o no tenés permisos para responderlo"
        )

    return intercambio_actualizado