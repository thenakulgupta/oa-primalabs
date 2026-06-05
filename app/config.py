from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str = "sqlite:///./primalabs.db"
    provisioning_delay_seconds: float | None = None
    provisioning_delay_min: float = 9.0
    provisioning_delay_max: float = 10.0
    rate_limit_per_minute: int = 100
    input_token_price_per_1k: float = 0.001
    output_token_price_per_1k: float = 0.002


settings = Settings()
