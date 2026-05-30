from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.errors import DomainError


def register_exceptions_handlers(app: FastAPI) -> None:

    @app.exception_handler(DomainError)
    async def domain_error_exception_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )