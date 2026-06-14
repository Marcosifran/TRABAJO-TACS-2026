"""
Seed script — puebla el backend en memoria con datos de prueba.
Ejecutar después de levantar el backend:

    python seed.py
    python seed.py --url http://localhost:8000   # URL personalizada
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000/api/v1"

def parse_args():
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--url" and i + 1 < len(sys.argv) - 1:
            return sys.argv[i + 2]
    return BASE_URL

BASE_URL = parse_args()

# ── Credenciales de los usuarios sembrados ────────────────────────────────────
# El backend ya no usa el header legacy X-User-Token: nos logueamos con
# email/contraseña y usamos el JWT devuelto en Authorization: Bearer.

def load_env(path=".env"):
    valores = {}
    env_file = Path(path)
    if not env_file.exists():
        return valores
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            valores[key.strip()] = value.strip()
    return valores

env = load_env()
SEED_PASSWORD = env.get("SEED_USER_PASSWORD", "figuswap123")
EMAIL_U1 = "marcos@utn"
EMAIL_U2 = "jeronimo@utn"

# ── HTTP helper ───────────────────────────────────────────────────────────────

def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"  [WARN] {method} {path} → {e.code}: {body_err[:120]}")
        return None

def post(path, body, token):
    return request("POST", path, body, token)

def get(path, token):
    return request("GET", path, token=token)

def login(email, password):
    """Loguea un usuario sembrado y devuelve su JWT (access_token)."""
    resp = request("POST", "/auth/login", {"email": email, "password": password})
    if not resp or "access_token" not in resp:
        print(f"[ERROR] No se pudo loguear {email}. ¿Backend levantado y credenciales correctas?")
        sys.exit(1)
    return resp["access_token"]

TOKEN_U1 = login(EMAIL_U1, SEED_PASSWORD)
TOKEN_U2 = login(EMAIL_U2, SEED_PASSWORD)

# ── Datos de prueba ───────────────────────────────────────────────────────────

FIGURITAS_U1 = [
    {"numero": 10,  "equipo": "Argentina", "jugador": "Messi",      "cantidad": 3},
    {"numero": 11,  "equipo": "Argentina", "jugador": "Di María",    "cantidad": 2},
    {"numero": 22,  "equipo": "Brasil",    "jugador": "Neymar",      "cantidad": 2},
    {"numero": 30,  "equipo": "Francia",   "jugador": "Mbappé",      "cantidad": 1},
    {"numero": 41,  "equipo": "España",    "jugador": "Pedri",       "cantidad": 2},
    {"numero": 55,  "equipo": "Alemania",  "jugador": "Müller",      "cantidad": 1},
]

FIGURITAS_U2 = [
    {"numero": 7,   "equipo": "Portugal",  "jugador": "Ronaldo",     "cantidad": 3},
    {"numero": 10,  "equipo": "Argentina", "jugador": "Messi",       "cantidad": 1},
    {"numero": 9,   "equipo": "Uruguay",   "jugador": "Suárez",      "cantidad": 2},
    {"numero": 21,  "equipo": "Brasil",    "jugador": "Vinícius Jr", "cantidad": 2},
    {"numero": 34,  "equipo": "Francia",   "jugador": "Griezmann",   "cantidad": 1},
    {"numero": 15,  "equipo": "Colombia",  "jugador": "James Rdz",   "cantidad": 2},
]

FALTANTES_U1 = [
    {"numero_figurita": 7,  "equipo": "Portugal",  "jugador": "Ronaldo"},
    {"numero_figurita": 9,  "equipo": "Uruguay",   "jugador": "Suárez"},
    {"numero_figurita": 21, "equipo": "Brasil",    "jugador": "Vinícius Jr"},
]

FALTANTES_U2 = [
    {"numero_figurita": 10, "equipo": "Argentina", "jugador": "Messi"},
    {"numero_figurita": 30, "equipo": "Francia",   "jugador": "Mbappé"},
    {"numero_figurita": 41, "equipo": "España",    "jugador": "Pedri"},
]

# ── Seeding ───────────────────────────────────────────────────────────────────

def seed_usuario(token, nombre, figuritas, faltantes, tipo_pub="intercambio_directo", una_subasta=True):
    print(f"\n── {nombre} ──")
    album_ids = []

    # Álbum
    for fig in figuritas:
        r = post("/album/", fig, token)
        if r:
            album_ids.append(r)
            print(f"  ✓ Álbum: #{fig['numero']} {fig['jugador']}")

    # Publicaciones (todas menos la última si hay subasta)
    pub_ids = []
    for i, entry in enumerate(album_ids):
        tipo = "subasta" if (una_subasta and i == len(album_ids) - 1) else tipo_pub
        r = post("/publicaciones/", {
            "figurita_personal_id": entry["id"],
            "tipo_intercambio": tipo,
            "cantidad_disponible": 1,
        }, token)
        if r:
            pub_ids.append(r)
            print(f"  ✓ Publicación #{entry['numero']} [{tipo}]")

    # Faltantes
    for falt in faltantes:
        r = post("/usuarios/faltantes", falt, token)
        if r:
            print(f"  ✓ Faltante: #{falt['numero_figurita']} {falt['jugador']}")

    # Subasta para la última publicación tipo subasta
    if una_subasta and pub_ids:
        sub_pub = next((p for p in pub_ids if p.get("tipo_intercambio") == "subasta"), None)
        if sub_pub:
            inicio = datetime.now(timezone.utc)
            fin    = inicio + timedelta(hours=48)
            r = post("/subastas/", {
                "figurita_id": sub_pub["id"],
                "inicio": inicio.isoformat(),
                "fin":    fin.isoformat(),
            }, token)
            if r:
                print(f"  ✓ Subasta creada para pub #{sub_pub['id']}")

    return pub_ids

# ── Main ──────────────────────────────────────────────────────────────────────

print(f"Conectando a {BASE_URL} ...")

pubs_u1 = seed_usuario(TOKEN_U1, "Usuario 1", FIGURITAS_U1, FALTANTES_U1)
pubs_u2 = seed_usuario(TOKEN_U2, "Usuario 2", FIGURITAS_U2, FALTANTES_U2)

# Intercambio de prueba: U2 le propone un intercambio a U1
intercambio_pub_u1 = next((p for p in pubs_u1 if p.get("tipo_intercambio") == "intercambio_directo"), None)
intercambio_pub_u2 = next((p for p in pubs_u2 if p.get("tipo_intercambio") == "intercambio_directo"), None)

if intercambio_pub_u1 and intercambio_pub_u2:
    r = post("/intercambios/", {
        "figuritas_ofrecidas_numero": [intercambio_pub_u2["numero"]],
        "figurita_solicitada_numero": intercambio_pub_u1["numero"],
        "solicitado_a_id": 1,
    }, TOKEN_U2)
    if r:
        print(f"\n  ✓ Intercambio propuesto: U2 → U1")

print("\n✅ Seed completado.\n")
