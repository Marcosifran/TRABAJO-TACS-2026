"""
Tests unitarios — Maestro de Figuritas

Cubre:
- wikipedia_scraper._parsear: extracción de jugadores a partir de HTML controlado
- maestro_service: lógica de inicialización, lookup y refresh (con repos mockeados)
"""

import pytest
from unittest.mock import patch, MagicMock

from app.scraping.wikipedia_scraper import _parsear
from app.services import maestro_service


# ══════════════════════════════════════════
# HTML de prueba que imita la estructura de Wikipedia
# ══════════════════════════════════════════

_HTML_FIXTURE = """
<html><body>
<div id="mw-content-text">
  <h3><span class="mw-headline">Argentina</span></h3>
  <table class="wikitable">
    <tbody>
      <tr><th>#</th><th>Pos.</th><th>Player</th><th>Club</th></tr>
      <tr><td>1</td><td>GK</td><td>Emiliano Martínez</td><td>Aston Villa</td></tr>
      <tr><td>10</td><td>FW</td><td>Lionel Messi [c]</td><td>Inter Miami</td></tr>
      <tr><td>9</td><td>FW</td><td>Julián Álvarez</td><td>Atlético Madrid</td></tr>
    </tbody>
  </table>
  <h3><span class="mw-headline">Brazil</span></h3>
  <table class="wikitable">
    <tbody>
      <tr><th>#</th><th>Pos.</th><th>Player</th><th>Club</th></tr>
      <tr><td>10</td><td>FW</td><td>Vinícius Júnior</td><td>Real Madrid</td></tr>
      <tr><td>1</td><td>GK</td><td>Alisson</td><td>Liverpool</td></tr>
    </tbody>
  </table>
</div>
</body></html>
"""

_HTML_ANOTACIONES = """
<html><body>
<div id="mw-content-text">
  <h3><span class="mw-headline">France</span></h3>
  <table class="wikitable">
    <tbody>
      <tr><th>#</th><th>Pos.</th><th>Player</th><th>Club</th></tr>
      <tr><td>10</td><td>FW</td><td>Kylian Mbappé [c][a]</td><td>Real Madrid</td></tr>
      <tr><td>7</td><td>FW</td><td>Antoine Griezmann [b]</td><td>Atlético Madrid</td></tr>
    </tbody>
  </table>
</div>
</body></html>
"""

_HTML_VACIO = "<html><body><div id='mw-content-text'></div></body></html>"


# ══════════════════════════════════════════
# _parsear
# ══════════════════════════════════════════

class TestWikipediaScraper:

    def test_parsear_extrae_todos_los_jugadores(self):
        jugadores = _parsear(_HTML_FIXTURE)
        assert len(jugadores) == 5

    def test_parsear_numeros_son_globalmente_consecutivos(self):
        jugadores = _parsear(_HTML_FIXTURE)
        numeros = [j["numero"] for j in jugadores]
        assert numeros == list(range(1, len(jugadores) + 1))

    def test_parsear_ordena_por_numero_camiseta_dentro_del_equipo(self):
        jugadores = _parsear(_HTML_FIXTURE)
        arg = [j for j in jugadores if j["equipo"] == "Argentina"]
        camisetas = [j["numero_camiseta"] for j in arg]
        assert camisetas == sorted(camisetas)

    def test_parsear_continua_numeracion_entre_equipos(self):
        jugadores = _parsear(_HTML_FIXTURE)
        arg = [j for j in jugadores if j["equipo"] == "Argentina"]
        bra = [j for j in jugadores if j["equipo"] == "Brazil"]
        assert max(j["numero"] for j in arg) < min(j["numero"] for j in bra)

    def test_parsear_campos_correctos(self):
        jugadores = _parsear(_HTML_FIXTURE)
        messi = next(j for j in jugadores if j["jugador"] == "Lionel Messi")
        assert messi["equipo"] == "Argentina"
        assert messi["posicion"] == "FW"
        assert messi["numero_camiseta"] == 10
        assert isinstance(messi["numero"], int)

    def test_parsear_limpia_anotaciones_entre_corchetes(self):
        jugadores = _parsear(_HTML_ANOTACIONES)
        nombres = [j["jugador"] for j in jugadores]
        assert "Kylian Mbappé" in nombres
        assert "Antoine Griezmann" in nombres
        assert all("[" not in n for n in nombres)

    def test_parsear_html_sin_equipos_retorna_lista_vacia(self):
        assert _parsear(_HTML_VACIO) == []

    def test_parsear_ignora_equipos_duplicados(self):
        html_duplicado = _HTML_FIXTURE + _HTML_FIXTURE
        jugadores = _parsear(html_duplicado)
        equipos = [j["equipo"] for j in jugadores]
        assert equipos.count("Argentina") == 3  # 3 jugadores, no 6


# ══════════════════════════════════════════
# maestro_service
# ══════════════════════════════════════════

class TestMaestroService:

    def setup_method(self):
        maestro_service._inicializado = False

    def test_inicializar_no_scrape_si_coleccion_tiene_datos(self):
        with patch("app.services.maestro_service.maestro_repo.count", return_value=10), \
             patch("app.services.maestro_service.scrape_planteles") as mock_scrape:
            maestro_service.inicializar()
        mock_scrape.assert_not_called()

    def test_inicializar_scrape_si_coleccion_vacia(self):
        fake_jugadores = [{"numero": 1, "equipo": "X", "jugador": "Y", "posicion": "FW", "numero_camiseta": 1}]
        with patch("app.services.maestro_service.maestro_repo.count", return_value=0), \
             patch("app.services.maestro_service.scrape_planteles", return_value=fake_jugadores), \
             patch("app.services.maestro_service.maestro_repo.bulk_insert") as mock_insert:
            maestro_service.inicializar()
        mock_insert.assert_called_once_with(fake_jugadores)

    def test_inicializar_no_repite_si_ya_fue_llamado(self):
        with patch("app.services.maestro_service.maestro_repo.count", return_value=0), \
             patch("app.services.maestro_service.scrape_planteles", return_value=[]) as mock_scrape, \
             patch("app.services.maestro_service.maestro_repo.bulk_insert"):
            maestro_service.inicializar()
            maestro_service.inicializar()
        assert mock_scrape.call_count == 1

    def test_inicializar_falla_silenciosamente_si_scrape_lanza_excepcion(self):
        with patch("app.services.maestro_service.maestro_repo.count", return_value=0), \
             patch("app.services.maestro_service.scrape_planteles", side_effect=Exception("timeout")), \
             patch("app.services.maestro_service.maestro_repo.bulk_insert") as mock_insert:
            maestro_service.inicializar()  # no debe lanzar
        mock_insert.assert_not_called()

    def test_get_jugador_delega_en_repo(self):
        fake = {"numero": 47, "equipo": "Argentina", "jugador": "Messi", "posicion": "FW", "numero_camiseta": 10}
        with patch("app.services.maestro_service.maestro_repo.get_by_numero", return_value=fake) as mock:
            resultado = maestro_service.get_jugador(47)
        mock.assert_called_once_with(47)
        assert resultado == fake

    def test_get_jugador_retorna_none_si_no_existe(self):
        with patch("app.services.maestro_service.maestro_repo.get_by_numero", return_value=None):
            assert maestro_service.get_jugador(9999) is None

    def test_get_equipos_delega_en_repo(self):
        with patch("app.services.maestro_service.maestro_repo.get_equipos", return_value=["Argentina", "Brazil"]) as mock:
            resultado = maestro_service.get_equipos()
        mock.assert_called_once()
        assert resultado == ["Argentina", "Brazil"]

    def test_refresh_limpia_y_reinserta(self):
        fake = [{"numero": 1, "equipo": "X", "jugador": "Y", "posicion": "FW", "numero_camiseta": 1}]
        with patch("app.services.maestro_service.scrape_planteles", return_value=fake), \
             patch("app.services.maestro_service.maestro_repo.drop") as mock_drop, \
             patch("app.services.maestro_service.maestro_repo.bulk_insert") as mock_insert:
            total = maestro_service.refresh()
        mock_drop.assert_called_once()
        mock_insert.assert_called_once_with(fake)
        assert total == 1

    def test_refresh_propaga_excepcion_del_scraper(self):
        with patch("app.services.maestro_service.scrape_planteles", side_effect=Exception("network error")):
            with pytest.raises(Exception, match="network error"):
                maestro_service.refresh()
