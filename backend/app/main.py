from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dev_message_route import router as dev_message_route_router
from app.api.health import router as health_router
from app.api.system import router as system_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.spa_static import SpaStaticFiles, derive_reserved_roots
from app.modules.ai.routes import router as ai_router
from app.modules.ai.sensitivity_routes import router as sensitivity_router
from app.modules.bluecad.routes import router as bluecad_router
from app.modules.flowsheet.routes import router as flowsheet_router
from app.modules.local_ai.runtime.lifecycle import create_local_ai_runtime_lifecycle_from_env
from app.modules.memory.routes import router as memory_router
from app.modules.modeling.routes import router as modeling_router
from app.modules.project_knowledge.routes import router as project_knowledge_router
from app.modules.runner.recovery import reconcile_stranded_runner_jobs
from app.modules.runner.routes import router as runner_router
from app.modules.secrets.routes import router as secrets_router
from app.modules.workspaces.routes import router as workspaces_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    lifecycle = create_local_ai_runtime_lifecycle_from_env()
    app.state.local_ai_runtime_lifecycle = lifecycle
    try:
        await lifecycle.startup()
        reconcile_stranded_runner_jobs()
        yield
    finally:
        await lifecycle.shutdown()


def _frontend_dist_path() -> Path:
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local-first architecture spine for JarvisOS.",
        lifespan=lifespan,
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
    app.include_router(dev_message_route_router)
    app.include_router(ai_router)
    app.include_router(sensitivity_router)
    app.include_router(bluecad_router)
    app.include_router(secrets_router)
    app.include_router(workspaces_router)
    app.include_router(modeling_router)
    app.include_router(memory_router)
    app.include_router(runner_router)
    app.include_router(flowsheet_router)
    app.include_router(project_knowledge_router)

    frontend_dist = _frontend_dist_path()
    if frontend_dist.is_dir():
        reserved_roots = derive_reserved_roots(app.routes)
        app.mount(
            "/",
            SpaStaticFiles(directory=frontend_dist, reserved_roots=reserved_roots),
            name="frontend",
        )

    return app


app = create_app()