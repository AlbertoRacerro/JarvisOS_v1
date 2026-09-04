import asyncio
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
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
from app.modules.coding.runtime_routes import router as coding_runtime_router
from app.modules.coding.runtime_truth import (
    capture_runtime_snapshot,
    startup_snapshot_unavailable,
)
from app.modules.flowsheet.routes import router as flowsheet_router
from app.modules.local_ai.runtime.lifecycle import create_local_ai_runtime_lifecycle_from_env
from app.modules.memory.routes import router as memory_router
from app.modules.modeling.routes import router as modeling_router
from app.modules.project_knowledge.routes import router as project_knowledge_router
from app.modules.runner.local_python import execution_ownership_state
from app.modules.runner.recovery import (
    live_stranded_runner_working_dirs,
    reconcile_stranded_runner_jobs,
)
from app.modules.runner.routes import router as runner_router
from app.modules.secrets.routes import router as secrets_router
from app.modules.workspaces.routes import router as workspaces_router

RUNNER_RECOVERY_RECHECK_SECONDS = 0.25


async def _reconcile_after_live_owners_exit(
    working_dirs: tuple[Path, ...], *, poll_seconds: float = RUNNER_RECOVERY_RECHECK_SECONDS
) -> None:
    """Recheck only startup-observed live owners until each becomes non-live."""

    pending = set(working_dirs)
    while pending:
        await asyncio.sleep(poll_seconds)
        gone_paths: set[Path] = set()
        for working_dir in tuple(pending):
            state = execution_ownership_state(working_dir)
            if state == "live":
                continue
            if state == "gone":
                gone_paths.add(working_dir)
            else:
                pending.remove(working_dir)
        if not gone_paths:
            continue
        try:
            reconcile_stranded_runner_jobs()
        except sqlite3.OperationalError:
            # A transient SQLite lock must not discard the only follow-up for a
            # now-abandoned owner. Keep the gone paths pending and retry.
            continue
        pending.difference_update(gone_paths)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    lifecycle = create_local_ai_runtime_lifecycle_from_env()
    app.state.local_ai_runtime_lifecycle = lifecycle
    recovery_task: asyncio.Task[None] | None = None
    try:
        try:
            app.state.runtime_startup_snapshot = await asyncio.to_thread(
                capture_runtime_snapshot,
                provenance="process_start_observation",
            )
        except Exception:
            # Runtime-truth observation must never make JarvisOS fail to start.
            app.state.runtime_startup_snapshot = startup_snapshot_unavailable()
        await lifecycle.startup()
        live_working_dirs = live_stranded_runner_working_dirs()
        reconcile_stranded_runner_jobs()
        if live_working_dirs:
            recovery_task = asyncio.create_task(
                _reconcile_after_live_owners_exit(live_working_dirs)
            )
        yield
    finally:
        if recovery_task is not None:
            recovery_task.cancel()
            with suppress(asyncio.CancelledError):
                await recovery_task
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
    app.include_router(coding_runtime_router)

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
