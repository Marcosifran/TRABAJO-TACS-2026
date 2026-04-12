from fastapi import APIRouter, Depends
from app.schemas.intercambio_sch import IntercambioCreate
from app.dependencies import get_current_user
from app.services import intercambio_service
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

