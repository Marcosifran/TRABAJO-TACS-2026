import os
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000/api/v1")


async def _request(method: str, path: str, token: str | None, body: dict | None, params: dict | None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BACKEND_URL}{path}"
    kwargs = {"headers": headers, "params": params}
    if body is not None:
        kwargs["json"] = body
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await getattr(client, method)(url, **kwargs)
    try:
        data = response.json()
    except Exception:
        data = {}
    return response.status_code, data


async def api_get(path: str, token: str | None = None, params: dict | None = None):
    return await _request("get", path, token, None, params)


async def api_post(path: str, body: dict, token: str | None = None):
    return await _request("post", path, token, body, None)


async def api_patch(path: str, body: dict, token: str | None = None):
    return await _request("patch", path, token, body, None)


async def api_delete(path: str, token: str | None = None):
    return await _request("delete", path, token, None, None)
