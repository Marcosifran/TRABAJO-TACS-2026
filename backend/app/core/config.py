from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import ConfigDict

# Generamos una clase de configuración que hereda de BaseSettings de Pydantic.
# Permite cargar configuración desde un archivo .env o variables de entorno.
class Settings(BaseSettings):
    app_name: str = "Mundial Figuritas TACS"
    app_version: str = "2026.1"
    debug: bool = False

    # Contraseña de los usuarios sembrados (demo). Permite loguear a marcos/jeronimo
    # con el nuevo flujo JWT sin perder los datos asociados a sus ids 1 y 2.
    seed_user_password: str = "figuswap123"

    # Configuración JWT para el backend.
    jwt_secret: str = "dev-jwt-secret-change-me-please-use-env-overrides"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 480
    # Variables de MongoDB
    mongodb_url: str = "mongodb://localhost:27017" # Valor por defecto
    mongodb_db_name: str = "mundial_figuritas_db"

    cors_origins: list[str] = ["http://localhost:5173"]

    # Configuración moderna de Pydantic v2
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
    )

# Instanciamos settings
settings = Settings()