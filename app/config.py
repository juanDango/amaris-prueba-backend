from pydantic_settings import BaseSettings, SettingsConfigDict


# Definir las variables de ambiente
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    env: str = "dev"
    region: str = "us-east-1"

    # Variables de conexion a MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "btg"
    mongo_host: str = "mongodb://localhost:27017"

    # Variables para conexión de cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_client_secret: str = ""

    # Notificaciones variables
    ses_sender: str = "no-reply@example.com"

    # Seguridad JWT
    jwt_secret: str = "basic_secret"

    # Seguridad / CORS
    allowed_origins: str = "*"


    secret_mongo_db: str = "your_mongo_secret"



settings = Settings()  # sin _env_file en v2