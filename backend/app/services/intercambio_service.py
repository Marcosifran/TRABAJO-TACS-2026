from app.repositories import (
    album_repo,
    publicacion_repo,
    intercambio_repo,
    usuario_repo,
    calificacion_repo,
    faltante_repo,
)
from app.domain.intercambio import Intercambio
from app.domain.publicacion import Publicacion
from app.domain.errors import (
    DomainConflictError,
    DomainNotFoundError,
    DomainPermissionError,
    DomainValidationError,
)
from app.schemas import (
    FiguritaAlbumCreate,
    IntercambioCreate,
    IntercambioDecision,
    EstadoIntercambio,
    EstadoRespuestaIntercambio,
    TipoIntercambio,
)


def _intercambio_a_dict(intercambio: Intercambio, ya_calificado: bool = False) -> dict:
    return {
        "id": intercambio.id,
        "propuesto_por": intercambio.propuesto_por,
        "solicitado_a": intercambio.solicitado_a,
        "figuritas_ofrecidas": intercambio.figuritas_ofrecidas,
        "figurita_solicitada": intercambio.figurita_solicitada,
        "estado": intercambio.estado.value,
        "ya_calificado": ya_calificado,
    }


def validar_numeros_distintos(intercambio: IntercambioCreate) -> None:
    if intercambio.figurita_solicitada_numero in intercambio.figuritas_ofrecidas_numero:
        raise DomainValidationError(
            "La figurita solicitada no puede estar incluida entre las ofrecidas"
        )


def validar_usuario_destino(intercambio: IntercambioCreate, usuario_id: int) -> None:
    if intercambio.solicitado_a_id == usuario_id:
        raise DomainValidationError("No podés proponerte un intercambio a vos mismo")

    if not usuario_repo.get_by_id(intercambio.solicitado_a_id):
        raise DomainNotFoundError("El usuario destinatario no existe")


def obtener_publicaciones_para_intercambio(
    intercambio: IntercambioCreate,
    usuario_id: int,
) -> tuple[list[Publicacion], Publicacion]:
    todas_publicaciones = publicacion_repo.get_all()

    album_proponente = album_repo.get_by_user(usuario_id)
    numeros_en_album = {f.numero for f in album_proponente if f.cantidad > 0}

    numeros_faltantes = [
        n for n in intercambio.figuritas_ofrecidas_numero
        if n not in numeros_en_album
    ]

    if numeros_faltantes:
        raise DomainNotFoundError("No tenés en tu álbum todas las figuritas que ofrecés")

    for numero in intercambio.figuritas_ofrecidas_numero:
        if any(
            p.numero == numero
            and p.usuario_id == usuario_id
            and p.tipo_intercambio == TipoIntercambio.SUBASTA
            for p in todas_publicaciones
        ):
            raise DomainNotFoundError(f"La figurita {numero} está publicada como subasta")

    publicaciones_ofrecidas: list[Publicacion] = []

    publicacion_solicitada = next(
        (
            p for p in todas_publicaciones
            if p.numero == intercambio.figurita_solicitada_numero
            and p.usuario_id == intercambio.solicitado_a_id
            and p.tipo_intercambio == TipoIntercambio.INTERCAMBIO_DIRECTO
        ),
        None,
    )

    if not publicacion_solicitada:
        raise DomainNotFoundError(
            "El usuario destino no tiene publicada para intercambio directo la figurita solicitada"
        )

    return publicaciones_ofrecidas, publicacion_solicitada


def validar_cantidad_disponible(
    publicaciones_ofrecidas: list[Publicacion],
    publicacion_solicitada: Publicacion,
) -> None:
    if any(p.cantidad_disponible < 1 for p in publicaciones_ofrecidas):
        raise DomainValidationError("Alguna figurita ofrecida no tiene stock disponible")

    if publicacion_solicitada.cantidad_disponible < 1:
        raise DomainValidationError("La figurita solicitada no tiene stock disponible")


def validar_intercambio(
    intercambio: IntercambioCreate,
    usuario_id: int,
) -> tuple[list[Publicacion], Publicacion]:
    validar_numeros_distintos(intercambio)
    validar_usuario_destino(intercambio, usuario_id)
    publicaciones_ofrecidas, publicacion_solicitada = obtener_publicaciones_para_intercambio(
        intercambio, usuario_id
    )
    validar_cantidad_disponible(publicaciones_ofrecidas, publicacion_solicitada)
    return publicaciones_ofrecidas, publicacion_solicitada


def proponer_intercambio(intercambio: IntercambioCreate, usuario_id: int) -> dict:
    validar_intercambio(intercambio, usuario_id)
    creado = intercambio_repo.crear_intercambio(
        intercambio=intercambio,
        propuesto_por=usuario_id,
        solicitado_a=intercambio.solicitado_a_id,
    )
    return _intercambio_a_dict(creado)


def listar_intercambios_de(usuario_id: int) -> dict[str, list[dict]]:
    intercambios = intercambio_repo.listar_intercambios_por_usuario(usuario_id)
    resultado: dict[str, list[dict]] = {"enviados": [], "recibidos": []}
    for grupo in ("enviados", "recibidos"):
        for intercambio in intercambios.get(grupo, []):
            ya_calificado = bool(
                calificacion_repo.buscar_por_intercambio_y_calificador(intercambio.id, usuario_id)
            )
            resultado[grupo].append(_intercambio_a_dict(intercambio, ya_calificado=ya_calificado))
    return resultado


def _transferir_figurita(numero: int, de_usuario_id: int, a_usuario_id: int) -> None:
    fig = album_repo.get_by_number_and_user(numero, de_usuario_id)
    if fig:
        equipo, jugador = fig.equipo, fig.jugador
        resultado = album_repo.adjust_cantidad(fig.id, -1)
        if resultado is None:
            for p in publicacion_repo.get_all():
                if p.numero == numero and p.usuario_id == de_usuario_id:
                    publicacion_repo.delete(p.id)
        else:
            pub = next(
                (
                    p for p in publicacion_repo.get_all()
                    if p.numero == numero and p.usuario_id == de_usuario_id
                ),
                None,
            )
            if pub:
                publicacion_repo.adjust_cantidad(pub.id, -1)
    else:
        equipo, jugador = "Desconocido", "Desconocido"

    fig_dest = album_repo.get_by_number_and_user(numero, a_usuario_id)
    if fig_dest:
        album_repo.adjust_cantidad(fig_dest.id, 1)
    else:
        album_repo.create(
            FiguritaAlbumCreate(numero=numero, equipo=equipo, jugador=jugador, cantidad=1),
            usuario_id=a_usuario_id,
        )

    faltante_repo.remove_missing(a_usuario_id, numero)


def realizar_intercambio_aceptado(intercambio: Intercambio) -> None:
    for numero in intercambio.figuritas_ofrecidas:
        _transferir_figurita(numero, intercambio.propuesto_por, intercambio.solicitado_a)

    _transferir_figurita(
        intercambio.figurita_solicitada,
        intercambio.solicitado_a,
        intercambio.propuesto_por,
    )


def responder_intercambio(
    intercambio_id: str,
    decision: IntercambioDecision,
    usuario_id: int,
) -> dict:
    intercambio = intercambio_repo.find_exchange_by_id(intercambio_id)

    if not intercambio:
        raise DomainNotFoundError("Intercambio no encontrado")

    if intercambio.solicitado_a != usuario_id:
        raise DomainPermissionError("Solo el usuario receptor puede responder este intercambio")

    if intercambio.estado != EstadoIntercambio.PENDIENTE:
        raise DomainValidationError("El intercambio ya fue respondido")

    if decision.estado == EstadoRespuestaIntercambio.ACEPTADO:
        realizar_intercambio_aceptado(intercambio)

    intercambio_actualizado = intercambio_repo.answer_exchange(
        intercambio_id,
        decision.estado.value,
    )

    if not intercambio_actualizado:
        raise DomainConflictError("Intercambio no encontrado o no tenés permisos para responderlo")

    return _intercambio_a_dict(intercambio_actualizado)
