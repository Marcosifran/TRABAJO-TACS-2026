from app.repositories import (
    album_repo,
    publicacion_repo,
    intercambio_repo,
    usuario_repo,
    calificacion_repo,
    faltante_repo,
)
from app.domain.errors import (
    DomainConflictError,
    DomainNotFoundError,
    DomainPermissionError,
    DomainValidationError,
)
from app.schemas.intercambio_sch import IntercambioCreate, IntercambioDecision, EstadoIntercambio, EstadoRespuestaIntercambio
from app.schemas.album_sch import FiguritaAlbumCreate

def validar_numeros_distintos(intercambio: IntercambioCreate) -> None:
    """Valida que la figurita solicitada no esté incluida entre las ofrecidas."""
    if intercambio.figurita_solicitada_numero in intercambio.figuritas_ofrecidas_numero:
        raise DomainValidationError(
            "La figurita solicitada no puede estar incluida entre las ofrecidas"
        )


def validar_usuario_destino(intercambio: IntercambioCreate, usuario_id: int) -> None:
    """Valida que el usuario no se proponga un intercambio a sí mismo y que exista."""
    if intercambio.solicitado_a_id == usuario_id:
        raise DomainValidationError("No podés proponerte un intercambio a vos mismo")

    if not usuario_repo.get_by_id(intercambio.solicitado_a_id):
        raise DomainNotFoundError("El usuario destinatario no existe")


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
    album_proponente = album_repo.get_by_user(usuario_id)
    numeros_en_album = {f["numero"] for f in album_proponente if f["cantidad"] > 0}
    
    numeros_faltantes = [
        n for n in intercambio.figuritas_ofrecidas_numero
        if n not in numeros_en_album
    ]
    
    if numeros_faltantes:
        raise DomainNotFoundError("No tenés en tu álbum todas las figuritas que ofrecés")
    
    # NUEVO: Validar que no estén publicadas como SUBASTA
    for numero in intercambio.figuritas_ofrecidas_numero:
        if any(p["numero"] == numero and p["usuario_id"] == usuario_id and p["tipo_intercambio"] == "subasta" for p in todas_publicaciones):
            raise DomainNotFoundError(f"La figurita {numero} está publicada como subasta")

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
        raise DomainNotFoundError(
            "El usuario destino no tiene publicada para intercambio directo la figurita solicitada"
        )

    return publicaciones_ofrecidas, publicacion_solicitada


def validar_cantidad_disponible(
    publicaciones_ofrecidas: list[dict],
    publicacion_solicitada: dict,
) -> None:
    """Valida que todas las publicaciones involucradas tengan cantidad disponible."""
    if any(p["cantidad_disponible"] < 1 for p in publicaciones_ofrecidas):
        raise DomainValidationError("Alguna figurita ofrecida no tiene stock disponible")

    if publicacion_solicitada["cantidad_disponible"] < 1:
        raise DomainValidationError("La figurita solicitada no tiene stock disponible")


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
    validar_numeros_distintos(intercambio)
    validar_usuario_destino(intercambio, usuario_id)
    publicaciones_ofrecidas, publicacion_solicitada = obtener_publicaciones_para_intercambio(
        intercambio, usuario_id
    )
    validar_cantidad_disponible(publicaciones_ofrecidas, publicacion_solicitada)
    return publicaciones_ofrecidas, publicacion_solicitada


def proponer_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> dict:
    """Valida y persiste una propuesta de intercambio."""
    validar_intercambio(intercambio, usuario_id)
    return intercambio_repo.crear_intercambio(
        intercambio=intercambio,
        propuesto_por=usuario_id,
        solicitado_a=intercambio.solicitado_a_id,
    )


def listar_intercambios_de(usuario_id: int) -> dict[str, list[dict]]:
    """Devuelve intercambios enviados y recibidos con el flag de calificación."""
    intercambios = intercambio_repo.listar_intercambios_por_usuario(usuario_id)
    for grupo in ("enviados", "recibidos"):
        for intercambio in intercambios.get(grupo, []):
            intercambio["ya_calificado"] = bool(
                calificacion_repo.buscar_por_intercambio_y_calificador(intercambio["id"], usuario_id)
            )
    return intercambios


def _transferir_figurita(numero: int, de_usuario_id: int, a_usuario_id: int) -> None:
    """
    Transfiere una unidad de la figurita `numero` del cedente al receptor:
    - Resta (o elimina) del álbum del cedente y limpia sus publicaciones sin stock.
    - Suma (o crea) en el álbum del receptor.
    - Elimina la figurita de los faltantes del receptor.

    Cada transferencia es atómica en lógica de negocio; en Entrega 3 todo el loop
    de llamadas se envuelve en un único `with session.begin():`.
    """
    # 1. Restar del álbum del cedente
    fig = album_repo.get_by_number_and_user(numero, de_usuario_id)
    if fig:
        equipo, jugador = fig["equipo"], fig["jugador"]
        fig["cantidad"] -= 1
        if fig["cantidad"] <= 0:
            album_repo.delete(fig["id"])
            for pub in publicacion_repo.get_all():
                if pub["numero"] == numero and pub["usuario_id"] == de_usuario_id:
                    publicacion_repo.delete(pub["id"])
        else:
            pub = next(
                (p for p in publicacion_repo.get_all()
                 if p["numero"] == numero and p["usuario_id"] == de_usuario_id),
                None,
            )
            if pub:
                pub["cantidad_disponible"] -= 1
                if pub["cantidad_disponible"] <= 0:
                    publicacion_repo.delete(pub["id"])
    else:
        equipo, jugador = "Desconocido", "Desconocido"

    # 2. Sumar al álbum del receptor
    fig_dest = album_repo.get_by_number_and_user(numero, a_usuario_id)
    if fig_dest:
        fig_dest["cantidad"] += 1
    else:
        album_repo.create(
            FiguritaAlbumCreate(numero=numero, equipo=equipo, jugador=jugador, cantidad=1),
            usuario_id=a_usuario_id,
        )

    # 3. Eliminar de faltantes del receptor
    faltante_repo.remove_missing(a_usuario_id, numero)


def realizar_intercambio_aceptado(intercambio: dict) -> None:
    """
    Ejecuta el intercambio efectivo de figuritas entre los dos participantes.
    Delega cada transferencia individual a `_transferir_figurita`.
    """
    # Figuritas ofrecidas: proponente → solicitado_a
    for numero in intercambio["figuritas_ofrecidas"]:
        _transferir_figurita(numero, intercambio["propuesto_por"], intercambio["solicitado_a"])

    # Figurita solicitada: solicitado_a → proponente
    _transferir_figurita(
        intercambio["figurita_solicitada"],
        intercambio["solicitado_a"],
        intercambio["propuesto_por"],
    )

def responder_intercambio(
    intercambio_id: str,
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
    intercambio = intercambio_repo.find_exchange_by_id(intercambio_id)

    if not intercambio:
        raise DomainNotFoundError("Intercambio no encontrado")

    if intercambio["solicitado_a"] != usuario_id:
        raise DomainPermissionError("Solo el usuario receptor puede responder este intercambio")

    if intercambio["estado"] != EstadoIntercambio.PENDIENTE.value:
        raise DomainValidationError("El intercambio ya fue respondido")

    if decision.estado == EstadoRespuestaIntercambio.ACEPTADO:
        realizar_intercambio_aceptado(intercambio)

    intercambio_actualizado = intercambio_repo.answer_exchange(
        intercambio_id,
        decision.estado.value,
    )

    if not intercambio_actualizado:
        raise DomainConflictError("Intercambio no encontrado o no tenés permisos para responderlo")

    return intercambio_actualizado