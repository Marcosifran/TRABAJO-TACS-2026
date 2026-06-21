"""Mapeo de nombre de país (en inglés, como llega del maestro) a bandera emoji."""

# Nombre de equipo/país -> código ISO 3166-1 alpha-2.
# Incluye los participantes actuales del maestro más selecciones comunes
# para tolerar futuros refresh del scraping.
_ISO2 = {
    "Argentina": "AR",
    "Austria": "AT",
    "Belgium": "BE",
    "Bosnia and Herzegovina": "BA",
    "Brazil": "BR",
    "Cape Verde": "CV",
    "Colombia": "CO",
    "Croatia": "HR",
    "Curaçao": "CW",
    "Czech Republic": "CZ",
    "DR Congo": "CD",
    "France": "FR",
    "Haiti": "HT",
    "Ivory Coast": "CI",
    "Japan": "JP",
    "Jordan": "JO",
    "Mexico": "MX",
    "New Zealand": "NZ",
    "Paraguay": "PY",
    "Qatar": "QA",
    "South Korea": "KR",
    "Sweden": "SE",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Uzbekistan": "UZ",
    # Selecciones comunes adicionales
    "England": "GB",
    "Spain": "ES",
    "Germany": "DE",
    "Italy": "IT",
    "Netherlands": "NL",
    "Portugal": "PT",
    "United States": "US",
    "USA": "US",
    "Uruguay": "UY",
    "Chile": "CL",
    "Peru": "PE",
    "Ecuador": "EC",
    "Senegal": "SN",
    "Morocco": "MA",
    "Ghana": "GH",
    "Nigeria": "NG",
    "Cameroon": "CM",
    "Australia": "AU",
    "Canada": "CA",
    "Switzerland": "CH",
    "Denmark": "DK",
    "Poland": "PL",
    "Serbia": "RS",
    "Saudi Arabia": "SA",
    "Iran": "IR",
    "Egypt": "EG",
    "Algeria": "DZ",
}


def _iso2_a_emoji(iso2: str) -> str:
    """Convierte un código ISO2 (ej. 'AR') en su bandera emoji."""
    return "".join(chr(0x1F1E6 + (ord(c) - ord("A"))) for c in iso2.upper())


def bandera(equipo: str) -> str:
    """Bandera emoji del país; cadena vacía si no se conoce."""
    iso2 = _ISO2.get(equipo)
    return _iso2_a_emoji(iso2) if iso2 else ""
