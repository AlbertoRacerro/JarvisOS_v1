from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.system import router as system_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.ai.routes import router as ai_router
from app.modules.modeling.routes import router as modeling_router
from app.modules.runner.routes import router as runner_router
from app.modules.secrets.routes import router as secrets_router
from app.modules.workspaces.routes import router as workspaces_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local-first architecture spine for JarvisOS.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(system_router)
    app.include_router(ai_router)
    app.include_router(secrets_router)
    app.include_router(workspaces_router)
    app.include_router(modeling_router)
    app.include_router(runner_router)
    return app


app = create_app()
