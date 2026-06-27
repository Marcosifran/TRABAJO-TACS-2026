import random
import string

from locust import HttpUser, between, task

BASE = "/api/v1"
SEED_PASSWORD = "figuswap123"

# Equipos conocidos en el maestro (para búsquedas y faltantes)
EQUIPOS = [
    "Argentina", "Brasil", "España", "Francia", "Alemania",
    "México", "Colombia", "Uruguay", "Portugal", "Inglaterra",
]


def _email_aleatorio() -> str:
    sufijo = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"load_{sufijo}@test.com"


class UsuarioAnonimo(HttpUser):
    """Simula visitantes no registrados que solo consumen endpoints públicos."""

    weight = 1
    wait_time = between(1, 3)

    @task(3)
    def partidos(self):
        self.client.get(f"{BASE}/partidos/", name="GET /partidos/")

    @task(2)
    def estadisticas_publicas(self):
        self.client.get(f"{BASE}/estadisticas/publicas", name="GET /estadisticas/publicas")

    @task(1)
    def maestro(self):
        self.client.get(f"{BASE}/maestro/?limit=20", name="GET /maestro/")


class UsuarioNavegador(HttpUser):
    """Simula el usuario típico que navega el marketplace sin crear contenido."""

    weight = 5
    wait_time = between(1, 4)

    def on_start(self):
        self.token = None
        self.headers = {}

        email = _email_aleatorio()
        r = self.client.post(
            f"{BASE}/auth/register",
            json={"nombre": "Load", "email": email, "password": "loadtest123"},
            name="POST /auth/register",
        )
        if r.status_code == 200:
            self.token = r.json().get("access_token")
        else:
            # Fallback al seed user si el registro no está disponible
            r2 = self.client.post(
                f"{BASE}/auth/login",
                json={"email": "jeronimo@utn", "password": SEED_PASSWORD},
                name="POST /auth/login",
            )
            if r2.status_code == 200:
                self.token = r2.json().get("access_token")

        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(4)
    def ver_publicaciones(self):
        self.client.get(f"{BASE}/publicaciones/", headers=self.headers, name="GET /publicaciones/")

    @task(3)
    def ver_subastas(self):
        self.client.get(f"{BASE}/subastas/", headers=self.headers, name="GET /subastas/")

    @task(3)
    def ver_album(self):
        self.client.get(f"{BASE}/album/", headers=self.headers, name="GET /album/")

    @task(2)
    def ver_faltantes(self):
        self.client.get(
            f"{BASE}/usuarios/faltantes", headers=self.headers, name="GET /usuarios/faltantes"
        )

    @task(2)
    def buscar_por_equipo(self):
        equipo = random.choice(EQUIPOS)
        self.client.get(
            f"{BASE}/maestro/?equipo={equipo}",
            headers=self.headers,
            name="GET /maestro/?equipo=",
        )

    @task(1)
    def sugerencias(self):
        self.client.get(
            f"{BASE}/publicaciones/sugerencias",
            headers=self.headers,
            name="GET /publicaciones/sugerencias",
        )


class UsuarioActivo(HttpUser):
    """Simula al coleccionista que agrega figuritas, publica y registra faltantes."""

    weight = 2
    wait_time = between(2, 6)

    def on_start(self):
        self.token = None
        self.headers = {}
        self.jugadores = []

        email = _email_aleatorio()
        r = self.client.post(
            f"{BASE}/auth/register",
            json={"nombre": "Activo", "email": email, "password": "loadtest123"},
            name="POST /auth/register",
        )
        if r.status_code != 200:
            return

        self.token = r.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Cargar maestro para usar figuritas válidas en todos los requests
        mr = self.client.get(f"{BASE}/maestro/?limit=50", name="GET /maestro/ [setup]")
        if mr.status_code == 200:
            data = mr.json()
            self.jugadores = data if isinstance(data, list) else data.get("jugadores", [])

        # Agregar 3 figuritas iniciales para tener contenido desde el arranque
        for _ in range(3):
            self._agregar_figurita()

    def _agregar_figurita(self) -> str | None:
        """Agrega una figurita aleatoria del maestro al álbum. Devuelve el id si fue exitoso."""
        if not self.jugadores:
            return None
        j = random.choice(self.jugadores)
        r = self.client.post(
            f"{BASE}/album/",
            json={
                "numero": j["numero"],
                "equipo": j["equipo"],
                "jugador": j["jugador"],
                "cantidad": 2,
            },
            headers=self.headers,
            name="POST /album/",
        )
        return r.json().get("id") if r.status_code == 201 else None

    @task(4)
    def agregar_al_album(self):
        self._agregar_figurita()

    @task(3)
    def ver_mis_publicaciones(self):
        self.client.get(
            f"{BASE}/usuarios/publicaciones",
            headers=self.headers,
            name="GET /usuarios/publicaciones",
        )

    @task(2)
    def registrar_faltante(self):
        if not self.jugadores:
            return
        j = random.choice(self.jugadores)
        self.client.post(
            f"{BASE}/usuarios/faltantes",
            json={"numero_figurita": j["numero"]},
            headers=self.headers,
            name="POST /usuarios/faltantes",
        )

    @task(1)
    def publicar_figurita(self):
        """Agrega al álbum y la publica inmediatamente."""
        fid = self._agregar_figurita()
        if not fid:
            return
        self.client.post(
            f"{BASE}/publicaciones/",
            json={
                "figurita_personal_id": fid,
                "tipo_intercambio": "intercambio_directo",
                "cantidad_disponible": 1,
            },
            headers=self.headers,
            name="POST /publicaciones/",
        )
