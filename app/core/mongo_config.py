from app.core.config import env_with_secrets


class MongoConfig:
    MONGODB_URL: str = env_with_secrets.get("MONGODB_URL", "mongodb://0.0.0.0:27017")
    MONGO_PROD_DATABASE: str = env_with_secrets.get(
        "MONGO_PROD_DATABASE", "template_db"
    )

    # List all collections constants here
