class DomainError(Exception):
    status_code = 400


class DomainValidationError(DomainError):
    status_code = 400


class DomainNotFoundError(DomainError):
    status_code = 404


class DomainPermissionError(DomainError):
    status_code = 403


class DomainConflictError(DomainError):
    status_code = 409


class DomainAuthError(DomainError):
    status_code = 401
