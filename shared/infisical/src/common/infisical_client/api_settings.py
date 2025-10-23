from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    # Required: The URL of the Infisical instance
    INFISICAL_HOST: HttpUrl = "https://app.infisical.com"

    # Auth Method: Universal Auth
    INFISICAL_CLIENT_ID: str
    INFISICAL_CLIENT_SECRET: SecretStr

    model_config = SettingsConfigDict(case_sensitive=True)
