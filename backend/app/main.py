"""FastAPI entrypoint — wires base routes + discovered customer routers."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.routes.base import router as base_router
from app.customers import discover_customers, iter_customer_routers
from app.jobs.routes import router as jobs_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.run_migrations_on_startup:
        from app.core.migrate_all import migrate_all

        logger.info("Running migrate_all on startup (platform → base → customer)")
        migrate_all()
    discover_customers()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure customers are discovered before routers are mounted (tests / reloads)
    discover_customers()

    application.include_router(base_router, prefix="/api")
    application.include_router(jobs_router, prefix="/api")

    for customer_id, customer_router in iter_customer_routers():
        application.include_router(
            customer_router,
            prefix="/api",
            # Tag already set inside each customer module
        )
        application.state.customer_routers = getattr(
            application.state, "customer_routers", []
        ) + [customer_id]

    return application


app = create_app()
