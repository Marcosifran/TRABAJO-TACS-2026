from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.errors import DomainError

def register_exceptions_handlers(app: FastAPI) -> None:

    # Manejador global para ValueError 
    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request:Request, exc: ValueError):
        detail = str(exc)
        #Si el error dice "inexistente" o "no existe / no encontrada", se devuelve
        # HTTP 404. Para el resto de errores, HTTP 400
        status_code = 400
        detail_lower = detail.lower()
        if "inexistente" in detail_lower or "no encontrada" in detail_lower or "no existe" in detail_lower:
            status_code = 404
        elif "registrada como faltante" in detail_lower or "ya está registrada" in detail_lower:
            status_code = 409
        #retorna el stable error envelope
        return JSONResponse(
            status_code = status_code,
            content={"detail":detail},
        )

    # Manejador global para PermissionError
    @app.exception_handler(PermissionError)
    async def permission_error_exception_handler(request: Request, exc: PermissionError):
        #Todo error se traduce a HTTP 403
        return JSONResponse(
            status_code = 403,
            content={"detail":str(exc)},
        )
    # Manejador global DomainError
    @app.exception_handler(DomainError)
    async def domain_error_exception_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code = exc.status_code,
            content={"detail":str(exc)},
        )