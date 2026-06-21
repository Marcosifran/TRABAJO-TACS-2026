_sessions: dict[int, dict] = {}


def is_logged_in(user_id: int) -> bool:
    return user_id in _sessions


def get_token(user_id: int) -> str | None:
    sess = _sessions.get(user_id)
    return sess["token"] if sess else None


def get_usuario(user_id: int) -> dict | None:
    sess = _sessions.get(user_id)
    return sess["usuario"] if sess else None


def set_session(user_id: int, token: str, usuario: dict) -> None:
    _sessions[user_id] = {"token": token, "usuario": usuario}


def clear_session(user_id: int) -> None:
    _sessions.pop(user_id, None)
