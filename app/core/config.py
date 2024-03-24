import logging.config
from glob import glob
from os import environ as env
from typing import List

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv(".env")

unwanted_prefixes = [
    "ORG_STAG_",
    "STAG_ORG_",
    "ORG_PROD_",
    "PROD_ORG_",
    "STAG_TEMPLATE_",
    "PROD_TEMPLATE_",
    "ORG_",
]
for var in glob("/run/secrets/*"):
    k = var.split("/")[-1]
    for unwanted_prefix in unwanted_prefixes:
        if k.startswith(unwanted_prefix):
            k = k[len(unwanted_prefix) :]  # noqa
    v = open(var).read().rstrip("\n")
    env[k] = v


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: List = [
        "*",
        "http://localhost:4200",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5501/",
        "https://www.zupay.in/",
    ]

    PROJECT_NAME: str = env.get("PROJECT_NAME", "template-project")
    PROJECT_DESCRIPTION: str = env.get(
        "PROJECT_DESCRIPTION", "This is a dummy template project"
    )
    API_ROOT_PATH: str = env.get("API_ROOT_PATH", "")

    SENTRY_DNS: str = env.get("SENTRY_DNS", "")

    AUTH_SERVICE_URL: str = env.get("AUTH_SERVICE_URL", "")

    ENV: str = env.get("ENV", "DEV")

    class Config:
        case_sensitive = True


settings = Settings()
env_with_secrets = env


class RedisConfig:
    settings = Settings()
    CLIENT_NAME: str = env_with_secrets.get("PROJECT_NAME").replace(" ", "_")
    REDIS_HOST: str = env_with_secrets.get("REDIS_HOST", None)
    REDIS_PORT: str = env_with_secrets.get("REDIS_PORT", "6379")
    REDIS_DB: str = env_with_secrets.get("REDIS_DB", "0")
    REDIS_USER: str = env_with_secrets.get("REDIS_USER", "")
    REDIS_PASSWORD: str = env_with_secrets.get("REDIS_PASSWORD", "")
    REDIS_CACHE_DB: str = env_with_secrets.get("REDIS_CACHE_DB", "9")
    REDIS_USE_SENTINEL: bool = False


class HealthCheckEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/ping") == -1


public_key = env.get("JWT_PUBLIC_KEY", None)
if public_key is None:
    with open("public.pem", mode="rb") as public_pem:
        public_key = public_pem.read()

private_key = env.get("JWT_PRIVATE_KEY", None)
if private_key is None:
    with open("private.pem", mode="r") as private_pem:
        private_key = private_pem.read()


class AuthJWTSettings(BaseSettings):
    authjwt_algorithm: str = "RS512"
    authjwt_public_key: str = public_key
    authjwt_private_key: str = private_key


auth_jwt_settings = AuthJWTSettings()
# Filter out /ping endpoint
logging.getLogger("uvicorn.access").addFilter(HealthCheckEndpointFilter())
