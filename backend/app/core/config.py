from pydantic_settings import BaseSettings

''' Generamos una clase de configuración que hereda de BaseSettings de Pydantic. Esto es para poder
cargar la configuración desde un archivo .env (en la raíz o desde variables de entorno.'''
class Settings(BaseSettings):
    app_name: str = "Mundial Figuritas TACS"
    app_version: str = "2026.1"
    debug: bool = False

    # Tokens de cada usuario. Se cargan desde .env de la raíz.
    user_1_token: str
    user_2_token: str

    class Config:
        # Busca el .env primero en backend/ (ejecución local) y luego en la raíz (Docker)
        env_file = (".env", "../.env")

# Instanciamos settings.
settings = Settings()
