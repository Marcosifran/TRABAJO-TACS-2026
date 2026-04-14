from fastapi import HTTPException

from app.repositories import figurita_repo, intercambio_repo, usuario_repo
from app.schemas.intercambio_sch import IntercambioCreate, IntercambioDecision


def validar_figuritas_ofrecidas(intercambio: IntercambioCreate) -> None:
    if not intercambio.figuritas_ofrecidas_numero:
        raise HTTPException(status_code=400, detail="Debés ofrecer al menos una figurita")

    if len(intercambio.figuritas_ofrecidas_numero) != len(set(intercambio.figuritas_ofrecidas_numero)):
        raise HTTPException(status_code=400, detail="No podés repetir figuritas en la oferta")


def validar_numeros_distintos(intercambio: IntercambioCreate) -> None:
    '''
    Validamos que la figurita solicitada no esté incluida entre las ofrecidas.
    '''
    if intercambio.figurita_solicitada_numero in intercambio.figuritas_ofrecidas_numero:
        raise HTTPException(status_code=400, detail="La figurita solicitada no puede estar incluida entre las ofrecidas")


def validar_usuario_destino(intercambio: IntercambioCreate, usuario_id: int) -> None:
    if intercambio.solicitado_a_id == usuario_id:
        raise HTTPException(status_code=400, detail="No podés proponerte un intercambio a vos mismo")


def obtener_figuritas_para_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> tuple[list[dict], dict]: 
    '''
    Obtiene de los repositorios las figuritas ofrecidas y la solicitada para un intercambio.
    '''   
    todas = figurita_repo.get_all()

    figuritas_ofrecidas = [
        f
        for f in todas
        if f["numero"] in intercambio.figuritas_ofrecidas_numero and f["usuario_id"] == usuario_id
    ]

    figurita_solicitada = next(
        (
            f
            for f in todas
            if f["numero"] == intercambio.figurita_solicitada_numero
            and f["usuario_id"] == intercambio.solicitado_a_id
        ),
        None, # Si no encuentra la figurita ofrecida del usuario, devuelve None
    )

    numeros_ofrecidos_encontrados = {f["numero"] for f in figuritas_ofrecidas}
    numeros_faltantes = [
        numero
        for numero in intercambio.figuritas_ofrecidas_numero
        if numero not in numeros_ofrecidos_encontrados
    ]

    if numeros_faltantes:
        raise HTTPException(status_code=404, detail="No tenés publicadas todas las figuritas que ofrecés")

    if not figurita_solicitada:
        raise HTTPException(status_code=404, detail="El usuario destino no tiene publicada la figurita solicitada")

    return figuritas_ofrecidas, figurita_solicitada


def validar_cantidad_disponible(figuritas_ofrecidas: list[dict], figurita_solicitada: dict) -> None:
    '''
    Validamos que todas las figuritas ofrecidas y la solicitada tengan cantidad disponible para intercambio.
    '''
    if any(figurita_ofrecida["cantidad"] < 1 for figurita_ofrecida in figuritas_ofrecidas):
        raise HTTPException(status_code=400, detail="Alguna figurita ofrecida no tiene stock disponible")

    if figurita_solicitada["cantidad"] < 1:
        raise HTTPException(status_code=400, detail="La figurita solicitada no tiene stock disponible")


def validar_tipo_intercambio(figuritas_ofrecidas: list[dict], figurita_solicitada: dict) -> None:
    '''
    Validamos que todas las figuritas ofrecidas y la solicitada estén configuradas para intercambio directo.
    '''
    if any(figurita_ofrecida["tipo_intercambio"] != "intercambio_directo" for figurita_ofrecida in figuritas_ofrecidas):
        raise HTTPException(status_code=400, detail="Alguna figurita ofrecida no está configurada para intercambio directo")

    if figurita_solicitada["tipo_intercambio"] != "intercambio_directo":
        raise HTTPException(status_code=400, detail="La figurita solicitada no está configurada para intercambio directo")


def validar_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> tuple[list[dict], dict]:
    '''
    Validamos que un intercambio propuesto cumpla con las reglas de negocio
    Devuelve las figuritas involucradas en el intercambio para que puedan ser utilizadas posteriormente en la creación del mismo.

    Reglas: 
        - Que la lista de figuritas ofrecidas no esté vacía
        - Que la figurita solicitada no esté dentro de las ofrecidas
        - Que el usuario tenga publicadas todas las figuritas que ofrece
        - Que el usuario destino tenga publicada la figurita que solicita
        - Que todas las figuritas involucradas tengan cantidad disponible para intercambio
        - Que todas las figuritas involucradas estén configuradas para intercambio directo
    
    '''
    validar_figuritas_ofrecidas(intercambio)
    validar_numeros_distintos(intercambio)
    validar_usuario_destino(intercambio, usuario_id)
    figuritas_ofrecidas, figurita_solicitada = obtener_figuritas_para_intercambio(intercambio, usuario_id)
    validar_cantidad_disponible(figuritas_ofrecidas, figurita_solicitada)
    validar_tipo_intercambio(figuritas_ofrecidas, figurita_solicitada)
    return figuritas_ofrecidas, figurita_solicitada


def realizar_intercambio_aceptado(intercambio: dict) -> None:
    '''
    Realiza el intercambio entre los usuarios, actualizando la propiedad usuario_id de las figuritas ofrecida y solicitada.
    Además, si las figuritas recibidas estaban marcadas como faltantes por alguno de los usuarios, las removemos de su lista de faltantes.
    '''

    figuritas_ofrecidas = []
    for numero_ofrecido in intercambio["figuritas_ofrecidas"]:
        figurita_ofrecida = figurita_repo.buscar_por_numero_y_usuario(
            numero=numero_ofrecido,
            usuario_id=intercambio["propuesto_por"],
        )
        if not figurita_ofrecida:
            raise HTTPException(
                status_code=404,
                detail="No se pudo concretar el intercambio porque faltan figuritas publicadas",
            )
        figuritas_ofrecidas.append(figurita_ofrecida)

    # Obtengo la figurita solicitada
    figurita_solicitada = figurita_repo.buscar_por_numero_y_usuario(
        numero=intercambio["figurita_solicitada"],
        usuario_id=intercambio["solicitado_a"],
    )

    if not figurita_solicitada:
        raise HTTPException(
            status_code=404,
            detail="No se pudo concretar el intercambio porque faltan figuritas publicadas",
        )

    # Transferimos las figuritas ofrecidas al receptor.
    for figurita_ofrecida in figuritas_ofrecidas:
        figurita_ofrecida["usuario_id"] = intercambio["solicitado_a"]

    # Transferimos la figurita solicitada al proponente.
    figurita_solicitada["usuario_id"] = intercambio["propuesto_por"]

    # Si las figuritas recibidas estaban marcadas como faltantes, las removemos.
    for numero_ofrecido in intercambio["figuritas_ofrecidas"]:
        usuario_repo.remove_faltante(
            usuario_id=intercambio["solicitado_a"],
            numero_figurita=numero_ofrecido,
        )

    usuario_repo.remove_faltante(
        usuario_id=intercambio["propuesto_por"],
        numero_figurita=intercambio["figurita_solicitada"],
    )


def responder_intercambio(intercambio_id: int, decision: IntercambioDecision, usuario_id: int) -> dict:
    '''
    Permite al usuario receptor de un intercambio responderlo, aceptándolo o rechazándolo.
    Validamos que :
        - el intercambio exista
        - que el usuario sea el receptor del mismo
        - el intercambio esté pendiente de respuesta.

    Devuelve el intercambio actualizado
    '''
    intercambio = intercambio_repo.buscar_intercambio_por_id(intercambio_id)

    if not intercambio:
        raise HTTPException(status_code=404, detail="Intercambio no encontrado")

    if intercambio["solicitado_a"] != usuario_id:
        raise HTTPException(status_code=403, detail="Solo el usuario receptor puede responder este intercambio")

    if intercambio["estado"] != "pendiente":
        raise HTTPException(status_code=400, detail="El intercambio ya fue respondido")

    if decision.estado.value == "aceptado":
        realizar_intercambio_aceptado(intercambio)


    intercambio_actualizado = intercambio_repo.responder_intercambio(intercambio_id, decision.estado.value)

    if not intercambio_actualizado:
        raise HTTPException(status_code=404, detail="Intercambio no encontrado o no tenés permisos para responderlo")

    return intercambio_actualizado
