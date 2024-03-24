import inspect
import re

from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.core.config import settings


def _get_auth_token_url() -> str:
    if settings.ENV == "PROD":
        return "https://auth-v2.api.zupay.in/auth/dummy_login"
    return "https://auth-v2.stag.apis.zupay.in/auth/dummy_login"


def set_custom_openapi(app):  # noqa
    """
    Sets a custom OpenAPI schema for the FastAPI application.

    This function generates a custom OpenAPI schema based on the provided FastAPI `app` object.
    The schema includes security schemes and applies them to routes based on certain conditions.

    Args:
        app: The FastAPI application object.

    Returns:
        None

    Examples:
        ```python
        app = FastAPI()

        # Setting the custom OpenAPI schema
        set_custom_openapi(app)
        ```
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=settings.PROJECT_NAME,
            version="2.0",
            description=settings.PROJECT_DESCRIPTION,
            routes=app.routes,
        )

        token_url: str = _get_auth_token_url()

        openapi_schema["components"] = openapi_schema.get("components", {}) or {}

        openapi_schema["components"]["securitySchemes"] = {
            "internal_api_key": {
                "type": "apiKey",
                "name": "internal_api_key",
                "in": "header",
            },
            "Bearer Auth": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "scopes": {},
                        "tokenUrl": token_url,
                    }
                },
            },
        }
        # Get all routes where jwt_optional() or jwt_required
        api_router = [route for route in app.routes if isinstance(route, APIRoute)]

        for route in api_router:
            path = getattr(route, "path")
            endpoint = getattr(route, "endpoint")
            methods = [method.lower() for method in getattr(route, "methods")]

            for method in methods:
                if (
                    re.search("jwt_required", inspect.getsource(endpoint))
                    or re.search("fresh_jwt_required", inspect.getsource(endpoint))
                    or re.search("jwt_optional", inspect.getsource(endpoint))
                    or re.search("AuthJWT", inspect.getsource(endpoint))
                ):
                    openapi_schema["paths"][path][method]["security"] = [
                        {"Bearer Auth": []}
                    ]
                elif re.search("APIKey", inspect.getsource(endpoint)):
                    openapi_schema["paths"][path][method]["security"] = [
                        {"internal_api_key": []}
                    ]

        return openapi_schema

    app.openapi = custom_openapi
