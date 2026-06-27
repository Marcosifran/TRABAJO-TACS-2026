"""
Cliente para la API de football-data.org v4.
Obtiene los partidos del Mundial 2026 y los mapea al formato interno.
"""
import requests
from datetime import datetime, timezone, timedelta
from app.core.config import settings

_BA_TZ = timezone(timedelta(hours=-3))

_BASE_URL = "https://api.football-data.org/v4"

_STAGE_MAP = {
    "GROUP_STAGE": "Grupo",
    "LAST_32": "Dieciseisavos",
    "LAST_16": "Octavos",
    "ROUND_OF_16": "Octavos",
    "QUARTER_FINALS": "Cuartos",
    "SEMI_FINALS": "Semifinal",
    "THIRD_PLACE": "Tercer puesto",
    "FINAL": "Final",
}

_GROUP_LETTER = {f"GROUP_{c}": c for c in "ABCDEFGHIJKLMNOP"}

_NOMBRES_ES = {
    "Mexico": "México",
    "United States": "USA",
    "Canada": "Canadá",
    "Morocco": "Marruecos",
    "Spain": "España",
    "Netherlands": "Países Bajos",
    "France": "Francia",
    "Brazil": "Brasil",
    "Germany": "Alemania",
    "Japan": "Japón",
    "Korea Republic": "Corea del Sur",
    "South Korea": "Corea del Sur",
    "Portugal": "Portugal",
    "Denmark": "Dinamarca",
    "England": "Inglaterra",
    "Iran": "Irán",
    "Belgium": "Bélgica",
    "Croatia": "Croacia",
    "Turkey": "Turquía",
    "Türkiye": "Turquía",
    "Poland": "Polonia",
    "Saudi Arabia": "Arabia Saudita",
    "Cameroon": "Camerún",
    "Côte d'Ivoire": "Costa de Marfil",
    "Ivory Coast": "Costa de Marfil",
    "Panama": "Panamá",
    "Peru": "Perú",
    "Nigeria": "Nigeria",
    "Senegal": "Senegal",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Uruguay": "Uruguay",
    "Colombia": "Colombia",
    "Venezuela": "Venezuela",
    "Ghana": "Ghana",
    "Serbia": "Serbia",
    "Bolivia": "Bolivia",
    "Jamaica": "Jamaica",
    "Ecuador": "Ecuador",
    "Australia": "Australia",
    "Switzerland": "Suiza",
    "Uzbekistan": "Uzbekistán",
    "Congo DR": "Congo RD",
    "New Zealand": "Nueva Zelanda",
    "Paraguay": "Paraguay",
    "South Africa": "Sudáfrica",
    "Czechia": "República Checa",
    "Czech Republic": "República Checa",
    "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "Algeria": "Argelia",
    "Egypt": "Egipto",
    "Haiti": "Haití",
    "Iraq": "Irak",
    "Jordan": "Jordania",
    "Norway": "Noruega",
    "Qatar": "Catar",
    "Scotland": "Escocia",
    "Sweden": "Suecia",
    "Tunisia": "Túnez",
    "Cape Verde Islands": "Cabo Verde",
    "Cape Verde": "Cabo Verde",
    "Curaçao": "Curazao",
    "Austria": "Austria",
    "Russia": "Rusia",
    "Wales": "Gales",
    "Northern Ireland": "Irlanda del Norte",
    "Republic of Ireland": "Irlanda",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "El Salvador": "El Salvador",
    "Trinidad and Tobago": "Trinidad y Tobago",
    "Cuba": "Cuba",
    "Guatemala": "Guatemala",
    "Bahrain": "Baréin",
    "Oman": "Omán",
    "United Arab Emirates": "Emiratos Árabes",
    "Kuwait": "Kuwait",
}


def _nombre_es(nombre: str) -> str:
    return _NOMBRES_ES.get(nombre, nombre)


def _mapear_partido(m: dict) -> dict:
    stage = m.get("stage", "")
    group = m.get("group") or ""

    if stage == "GROUP_STAGE":
        letra = _GROUP_LETTER.get(group, group.replace("GROUP_", ""))
        fase = f"Grupo {letra}"
    else:
        fase = _STAGE_MAP.get(stage, stage)

    utc_date = m.get("utcDate", "")
    fecha = ""
    hora = ""
    if utc_date:
        try:
            dt_utc = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
            dt_ba = dt_utc.astimezone(_BA_TZ)
            fecha = dt_ba.strftime("%Y-%m-%d")
            hora = dt_ba.strftime("%H:%M")
        except ValueError:
            fecha = utc_date[:10]
            hora = utc_date[11:16]

    score = m.get("score", {}) or {}
    ft = score.get("fullTime") or {}

    return {
        "id": m.get("id"),
        "fase": fase,
        "fecha": fecha,
        "hora": hora,
        "local": _nombre_es((m.get("homeTeam") or {}).get("name") or "?"),
        "visitante": _nombre_es((m.get("awayTeam") or {}).get("name") or "?"),
        "estadio": m.get("venue"),
        "ciudad": None,
        "estado": m.get("status"),
        "goles_local": ft.get("home"),
        "goles_visitante": ft.get("away"),
    }


def fetch_partidos_wc() -> list[dict]:
    """Descarga los partidos del Mundial 2026 desde football-data.org."""
    if not settings.football_data_api_key:
        raise ValueError("FOOTBALL_DATA_API_KEY no está configurada en el entorno")

    resp = requests.get(
        f"{_BASE_URL}/competitions/WC/matches",
        headers={"X-Auth-Token": settings.football_data_api_key},
        timeout=15,
    )

    restantes = resp.headers.get("X-Requests-Available-Minute")
    if restantes is not None:
        print(f"[football-api] Requests disponibles este minuto: {restantes}")

    resp.raise_for_status()
    return [_mapear_partido(m) for m in resp.json().get("matches", [])]
