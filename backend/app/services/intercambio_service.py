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

    # Buscamos las publicaciones del proponente que coincidan con los números ofrecidos
    publicaciones_ofrecidas = [
        p for p in todas_publicaciones
        if p["numero"] in intercambio.figuritas_ofrecidas_numero
        and p["usuario_id"] == usuario_id
        and p["tipo_intercambio"] == "intercambio_directo"
    ]

    # Verificamos que se encontraron todas las figuritas ofrecidas
    numeros_encontrados = {p["numero"] for p in publicaciones_ofrecidas}
    numeros_faltantes = [
        n for n in intercambio.figuritas_ofrecidas_numero
        if n not in numeros_encontrados
    ]
    if numeros_faltantes:
        raise HTTPException(
            status_code=404,
            detail="No tenés publicadas para intercambio directo todas las figuritas que ofrecés"
        )

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
    Transfiere la propiedad de las figuritas en el álbum al aceptar el intercambio.
    También elimina las figuritas recibidas de la lista de faltantes si estaban registradas.

    El intercambio opera sobre el álbum — cambia el usuario_id de cada figurita.
    """
    figuritas_ofrecidas = []
    for numero in intercambio["figuritas_ofrecidas"]:
        figurita = album_repo.get_por_numero_y_usuario(
            numero=numero,
            usuario_id=intercambio["propuesto_por"],
        )
        if not figurita:
            raise HTTPException(
                status_code=404,
                detail="No se pudo concretar el intercambio porque faltan figuritas en el álbum",
            )
        figuritas_ofrecidas.append(figurita)

    figurita_solicitada = album_repo.get_por_numero_y_usuario(
        numero=intercambio["figurita_solicitada"],
        usuario_id=intercambio["solicitado_a"],
    )
    if not figurita_solicitada:
        raise HTTPException(
            status_code=404,
            detail="No se pudo concretar el intercambio porque faltan figuritas en el álbum",
        )

    # Transferimos las figuritas ofrecidas al receptor
    for figurita in figuritas_ofrecidas:
        figurita["usuario_id"] = intercambio["solicitado_a"]

    # Transferimos la figurita solicitada al proponente
    figurita_solicitada["usuario_id"] = intercambio["propuesto_por"]

    # Si las figuritas recibidas estaban como faltantes, las removemos
    for numero in intercambio["figuritas_ofrecidas"]:
        usuario_repo.remove_faltante(
            usuario_id=intercambio["solicitado_a"],
            numero_figurita=numero,
        )

    usuario_repo.remove_faltante(
        usuario_id=intercambio["propuesto_por"],
        numero_figurita=intercambio["figurita_solicitada"],
    )


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