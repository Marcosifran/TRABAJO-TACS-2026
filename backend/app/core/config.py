from pydantic_settings import BaseSettings

''' Generamos una clase de configuración que hereda de BaseSettings de Pydantic. Esto es para poder
cargar la configuración desde un archivo .env (en la raíz o desde variables de entorno.'''
class Settings(BaseSettings):
    app_name: str = "Mundial Figuritas TACS"
    app_version: str = "2026.1"
    debug: bool = False

    class Config:
        env_file = ".env" # Por el momento no lo vamos a usar, es para la base de datos

# Instanciamos settings.
settings = Settings()
