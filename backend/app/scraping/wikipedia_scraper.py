"""
Scraper del plantel del Mundial FIFA 2026 desde Wikipedia.

Asigna números de figurita secuenciales (orden de aparición en la página,
dentro de cada equipo ordenado por número de camiseta). Los números son
asignados una sola vez y persisten en MongoDB — no deben cambiar después
del primer scraping en producción.
"""

import re
import requests
from bs4 import BeautifulSoup

_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
_HEADERS = {"User-Agent": "TACS-2026-Bot/1.0 (educational project)"}



def scrape_planteles() -> list[dict]:
    """Descarga y parsea el plantel del Mundial 2026 desde Wikipedia."""
    resp = requests.get(_URL, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return _parsear(resp.text)


def _parsear(html: str) -> list[dict]:
    """
    Extrae jugadores del HTML de la página de planteles de Wikipedia.
    Retorna lista de dicts con: numero, equipo, jugador, posicion, numero_camiseta.

    Estructura esperada de la página:
      h2 = Grupo (ej. "Group A")
      h3 > span.mw-headline = Equipo (ej. "Argentina")
      table.wikitable = plantel con columnas: No. | Pos. | Player | ...
    """
    soup = BeautifulSoup(html, "html.parser")
    contenido = soup.find("div", id="mw-content-text") or soup

    jugadores: list[dict] = []
    numero_figurita = 1
    equipos_vistos: set[str] = set()

    for tabla in contenido.find_all("table", class_="wikitable"):
        # Solo filas directas de la tabla (o su thead/tbody), ignora tablas anidadas
        filas = [tr for tr in tabla.find_all("tr")
                 if tr.parent == tabla or tr.parent.parent == tabla]
        if len(filas) < 2:
            continue

        # Validar que sea tabla de plantel: primera columna "No." y segunda "Pos."
        # Las tablas de clasificación de grupo también tienen "Pos." pero como PRIMERA columna.
        cabecera = [c.get_text(strip=True).upper() for c in filas[0].find_all(["th", "td"])]
        if len(cabecera) < 2:
            continue
        if cabecera[0] not in {"NO.", "NO", "#", "N°"} or cabecera[1] not in {"POS.", "POS"}:
            continue

        # Parsear jugadores de la tabla
        jugadores_tabla: list[tuple[int, str, str]] = []
        for fila in filas[1:]:
            celdas = fila.find_all(["td", "th"])
            if len(celdas) < 3:
                continue
            texto_num = celdas[0].get_text(strip=True)
            if texto_num:
                try:
                    num_camiseta = int(texto_num)
                except ValueError:
                    continue  # fila rara con texto no numérico en col 0
            else:
                num_camiseta = len(jugadores_tabla) + 1  # sin número asignado → orden de aparición
            posicion = re.sub(r"^\d+", "", celdas[1].get_text(strip=True)).upper()
            nombre = re.sub(r"\[.*?\]", "", celdas[2].get_text(strip=True)).strip()
            if nombre:
                jugadores_tabla.append((num_camiseta, posicion, nombre))

        if not jugadores_tabla:
            continue

        # Buscar el h3 más cercano anterior como nombre del equipo
        equipo = None
        for prev in tabla.find_all_previous(["h2", "h3"]):
            span = prev.find("span", class_="mw-headline")
            texto = span.get_text(strip=True) if span else prev.get_text(strip=True)
            texto = re.sub(r"\[.*?\]", "", texto).strip()
            if texto:
                equipo = texto
                break

        if not equipo or equipo in equipos_vistos:
            continue

        equipos_vistos.add(equipo)
        jugadores_tabla.sort(key=lambda x: x[0])

        for num_camiseta, posicion, nombre in jugadores_tabla:
            jugadores.append({
                "numero": numero_figurita,
                "equipo": equipo,
                "jugador": nombre,
                "posicion": posicion,
                "numero_camiseta": num_camiseta,
            })
            numero_figurita += 1

    return jugadores
