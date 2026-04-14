from fastapi import APIRouter, HTTPException, Depends
from app.schemas.intercambio_sch import IntercambioCreate, IntercambioResponse, IntercambioDecision
from app.schemas.calificacion_sch import CalificacionCreate, CalificacionResponse
from app.dependencies import get_current_user
from app.services import intercambio_service, calificacion_service
from app.repositories import intercambio_repo
    
router = APIRouter(prefix="/intercambios", tags=["Intercambios"])


@router.post("/")

def proponer_intercambio( intercambio: IntercambioCreate, usuario: dict = Depends(get_current_user)):
    
    intercambio_service.validar_intercambio(
        intercambio=intercambio,
        usuario_id=usuario["id"],
    )

    intercambio_propuesto = intercambio_repo.crear_intercambio(
        intercambio=intercambio,
        propuesto_por=usuario["id"],
        solicitado_a=intercambio.solicitado_a_id,
    )

    return intercambio_propuesto


@router.get("/")
def listar_intercambios(usuario: dict = Depends(get_current_user)):
    intercambios = intercambio_repo.listar_intercambios_por_usuario(usuario["id"])
    return intercambios


@router.patch("/{intercambio_id}/estado", response_model = IntercambioResponse)
def responder_intercambio(intercambio_id: int, decision: IntercambioDecision, usuario: dict = Depends(get_current_user)):
    intercambio_actualizado = intercambio_service.responder_intercambio(
        intercambio_id=intercambio_id,
        decision=decision,
        usuario_id=usuario["id"],
    )

    if intercambio_actualizado is None:
        raise HTTPException(status_code=404, detail="Intercambio no encontrado o no tenés permisos para responderlo")

    return intercambio_actualizado


@router.post(
    "/{intercambio_id}/calificaciones",
    response_model=CalificacionResponse,
    status_code=201,
)
def calificar_tras_intercambio(
    intercambio_id: int,
    body: CalificacionCreate,
    usuario: dict = Depends(get_current_user),
):
    return calificacion_service.crear_calificacion(
        intercambio_id=intercambio_id,
        calificador_id=usuario["id"],
        data=body,
    )