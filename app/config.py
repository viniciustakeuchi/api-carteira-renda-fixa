from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://carteira:carteira@localhost:5432/carteira"
    jwt_secret: str = "troque-esta-chave-em-producao-0123456789"
    jwt_algoritmo: str = "HS256"
    jwt_expiracao_minutos: int = 60

    # Premissas padrão de mercado (% ao ano), usadas quando a requisição não informa.
    cdi_anual: Decimal = Decimal("14.90")
    selic_anual: Decimal = Decimal("15.00")
    ipca_anual: Decimal = Decimal("4.80")


settings = Settings()
