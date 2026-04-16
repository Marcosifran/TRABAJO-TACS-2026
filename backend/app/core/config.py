from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import ConfigDict

# Generamos una clase de configuración que hereda de BaseSettings de Pydantic.
# Permite cargar configuración desde un archivo .env o variables de entorno.
class Settings(BaseSettings):
    app_name: str = "Mundial Figuritas TACS"
    app_version: str = "2026.1"
    debug: bool = False

    # Tokens de cada usuario. Se cargan desde .env de la raíz.
    user_1_token: str = ""
    user_2_token: str = ""

    # Configuración moderna de Pydantic v2
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env")
    )

# Instanciamos settings
settings = Settings()