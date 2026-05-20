# SEC-01 — Token model: non-constant-time, non-rotatable, unsigned

**Severity:** C  ·  **Area:** Security  ·  **Effort:** S (immediate fix) → L (full Entrega 3 redesign)

## Diagnosis

The TP spec is explicit that auth is not the focus and that the team only needs a way to distinguish two users — so a fully-fledged OAuth2/JWT pipeline is **not** required for the current entrega. The problem is more specific than "you should be using JWT": the token model that *was* chosen has two failure modes that are independent of how minimal it is allowed to be.

**1. The token comparison is timing-attack-vulnerable.** `usuario_repo.py:23-24` resolves the header by iterating the user list and comparing tokens with Python's `==`:

```python
def get_by_token(token: str) -> dict | None:
    return next((u for u in _db_usuarios if u["token"] == token), None)
```

`str.__eq__` in CPython short-circuits on the first differing byte. The time it takes to reject a wrong token therefore leaks how many leading characters were correct. An attacker on a network with stable latency can recover the token byte-by-byte by sending many requests and measuring response time. This is a textbook side-channel; the standard library exists exactly to defend against it (`hmac.compare_digest`, which compares in time proportional to the *length* of the input, not the position of the first mismatch). The fix is one import and one call. It is worth doing *now*, even with two hardcoded users, because the muscle memory carries forward and because the tests already exercise this code path on every protected request.

**2. The model is "stateless by accident."** "Stateless auth" in the strict sense means the server can verify a token's authenticity without consulting any storage — typically by checking a cryptographic signature (JWT, Paseto, signed cookies). The current scheme has *no* session store, but it also has no signature: a token is just an opaque UUID looked up in a Python list seeded from env vars. That means there is no expiration (`exp`), no issuer (`iss`), no subject (`sub`), no scopes, no rotation, no revocation. If a token leaks (a server log, a CI artifact, a client-side `sessionStorage` exfiltration), the only mitigation is to redeploy with a new `.env`. This is fine for a 2-user demo and is consistent with the TP's stance — but the team should be able to *explain* what they gave up and what Entrega 3 would replace it with. A signed JWT with `exp`/`iat`/`sub`, verified in `get_current_user`, gives stateless verification *and* expiration without introducing a session table.

A third minor observation: `dependencies.py:7-11` raises `HTTPException` directly inside the dependency. That is fine, but it returns FastAPI's default `{"detail": "..."}` envelope — see [ERR-01](./ERR-01-error-handling.md) for the broader shape question. There is no `WWW-Authenticate` response header on the 401, which is what an RFC-compliant client expects.

## Evidence

- `backend/app/repositories/usuario_repo.py:23-24` — `u["token"] == token` (timing-attack-vulnerable comparison)
- `backend/app/dependencies.py:7-11` — auth dependency; returns 401 without `WWW-Authenticate` header
- `backend/app/repositories/usuario_repo.py:4-7` — tokens stored cleartext in module-level list, seeded from env vars
- `backend/app/core/config.py:11-13` — `user_1_token` / `user_2_token` strings from `.env`
- `.gitignore:13-15` — `.env` correctly excluded from VCS; that part is fine

## Recommendation

Two-step fix: a one-line patch today, and a sketch for Entrega 3 so the path is visible.

### Today: constant-time compare

```python
# backend/app/repositories/usuario_repo.py
import hmac

def get_by_token(token: str) -> dict | None:
    if not token:
        return None
    for u in _db_usuarios:
        stored = u["token"]
        if stored and hmac.compare_digest(stored, token):
            return u
    return None
```

`hmac.compare_digest` accepts both `str` and `bytes`, runs in time proportional to the *shorter* of the two inputs, and is the exact tool for comparing secrets. The early `if not token` guard avoids comparing against the empty string that the placeholder `user_1_token: str = ""` default in `core/config.py:12` would create if `.env` is missing — without it, every request from an unconfigured client would silently match a misconfigured user.

While you're in there, consider giving `dependencies.py:get_current_user` a `WWW-Authenticate: Bearer` header on the 401 — FastAPI accepts a `headers=` kwarg on `HTTPException`.

### Entrega 3: signed JWT + a clean seam

Sketch — not a full implementation, just the shape:

```python
# backend/app/security.py  (new file)
import jwt
from datetime import datetime, timezone, timedelta
from app.core.config import settings

ALG = "HS256"

def issue(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=8)},
        settings.jwt_secret,
        algorithm=ALG,
    )

def verify(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALG])
    return int(payload["sub"])
```

`dependencies.py:get_current_user` then becomes: `user_id = verify(x_user_token)` (catching `jwt.PyJWTError` and translating to 401), followed by a repo lookup. The repo no longer stores tokens at all. The TP-compliant "two users" model survives — the tokens just become short-lived and signed, with a stable `sub` claim binding them to a user.

## Why this approach

- **`hmac.compare_digest` costs nothing and removes a real CWE.** The alternative — keeping `==` because "we only have two users" — assumes the attacker doesn't get to choose the token shape, which the cleartext-in-env model already breaks. There is no scenario where `==` is the right choice on a secret.
- **The JWT sketch is a *seam*, not a rewrite.** The router signature (`usuario: dict = Depends(get_current_user)`) is unchanged. Only the body of the dependency moves. That means SEC-01 doesn't conflict with any of the ARCH reports — switching auth doesn't ripple through services. This is the value of having the dependency in `dependencies.py` already.
- **Don't roll your own crypto.** `PyJWT` is the boring default. Resist the temptation to "just add an HMAC of `user_id + secret`" — once you're encoding two fields, you have a poorly-shaped JWT. Use the library and skip the rediscovery.
