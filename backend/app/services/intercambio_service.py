from fastapi import HTTPException

from app.repositories import figurita_repo, intercambio_repo, usuario_repo
from app.schemas.intercambio_sch import IntercambioCreate, IntercambioDecision


def validar_numeros_distintos(intercambio: IntercambioCreate) -> None:
    '''
    Validamos que el número de figurita ofrecida y solicitada no sean el mismo, ya que no tendría sentido un intercambio directo en ese caso.
    '''
    if intercambio.figurita_ofrecida_numero == intercambio.figurita_solicitada_numero:
        raise HTTPException(status_code=400, detail="La figurita ofrecida y solicitada no pueden ser la misma")


def validar_usuario_destino(intercambio: IntercambioCreate, usuario_id: int) -> None:
    if intercambio.solicitado_a_id == usuario_id:
        raise HTTPException(status_code=400, detail="No podés proponerte un intercambio a vos mismo")


def obtener_figuritas_para_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> tuple[dict, dict]: 
    '''
    Obtiene de los repositorios las figuritas ofrecida y solicitada para un intercambio.
    '''   
    todas = figurita_repo.get_all()
    figurita_ofrecida = next(
        (f for f in todas if f["numero"] == intercambio.figurita_ofrecida_numero and f["usuario_id"] == usuario_id),
        None, # Si no encuentra la figurita ofrecida del usuario, devuelve None
    )
    figurita_solicitada = next(
        (
            f
            for f in todas
            if f["numero"] == intercambio.figurita_solicitada_numero
            and f["usuario_id"] == intercambio.solicitado_a_id
        ),
        None, # Si no encuentra la figurita ofrecida del usuario, devuelve None
    )

    if not figurita_ofrecida:
        raise HTTPException(status_code=404, detail="No tenés publicada la figurita que ofrecés")
    if not figurita_solicitada:
        raise HTTPException(status_code=404, detail="El usuario destino no tiene publicada la figurita solicitada")

    return figurita_ofrecida, figurita_solicitada


def validar_cantidad_disponible(figurita_ofrecida: dict, figurita_solicitada: dict) -> None:
    '''
    Validamos que tanto la figurita ofrecida como la solicitada tengan cantidad disponible para intercambio.
    '''
    if figurita_ofrecida["cantidad"] < 1:
        raise HTTPException(status_code=400, detail="La figurita ofrecida no tiene stock disponible")
    if figurita_solicitada["cantidad"] < 1:
        raise HTTPException(status_code=400, detail="La figurita solicitada no tiene stock disponible")


def validar_tipo_intercambio(figurita_ofrecida: dict, figurita_solicitada: dict) -> None:
    '''
    Validamos que tanto la figurita ofrecida como la solicitada estén configuradas para intercambio directo.
    '''
    if figurita_ofrecida["tipo_intercambio"] != "intercambio_directo":
        raise HTTPException(status_code=400, detail="Tu figurita ofrecida no está configurada para intercambio directo")
    if figurita_solicitada["tipo_intercambio"] != "intercambio_directo":
        raise HTTPException(status_code=400, detail="La figurita solicitada no está configurada para intercambio directo")


def validar_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> tuple[dict, dict]:
    '''
    Validamos que un intercambio propuesto cumpla con las reglas de negocio
    Devuelve las figuritas involucradas en el intercambio para que puedan ser utilizadas posteriormente en la creación del mismo.
    '''
    validar_numeros_distintos(intercambio)
    validar_usuario_destino(intercambio, usuario_id)
    figurita_ofrecida, figurita_solicitada = obtener_figuritas_para_intercambio(intercambio, usuario_id)
    validar_cantidad_disponible(figurita_ofrecida, figurita_solicitada)
    validar_tipo_intercambio(figurita_ofrecida, figurita_solicitada)
    return figurita_ofrecida, figurita_solicitada


def realizar_intercambio_aceptado(intercambio: dict) -> None:
    # Obtengo la figurita ofrecida
    figurita_ofrecida = figurita_repo.buscar_por_numero_y_usuario(
        numero=intercambio["figurita_ofrecida"],
        usuario_id=intercambio["propuesto_por"],
    )
    # Obtengo la figurita solicitada
    figurita_solicitada = figurita_repo.buscar_por_numero_y_usuario(
        numero=intercambio["figurita_solicitada"],
        usuario_id=intercambio["solicitado_a"],
    )

    if not figurita_ofrecida or not figurita_solicitada:
        raise HTTPException(
            status_code=404,
            detail="No se pudo concretar el intercambio porque faltan figuritas publicadas",
        )

    # Las intercambio entre los usuarios
    figurita_ofrecida["usuario_id"] = intercambio["solicitado_a"]
    figurita_solicitada["usuario_id"] = intercambio["propuesto_por"]

    # Si las figuritas recibidas estaban marcadas como faltantes, las removemos.
    usuario_repo.remove_faltante(
        usuario_id=intercambio["solicitado_a"],
        numero_figurita=intercambio["figurita_ofrecida"],
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
