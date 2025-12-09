from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.reports import router as reports_router


def create_app() -> FastAPI:
    app = FastAPI(title="Annual Report Backend")
    app.include_router(reports_router)
    return app


app = create_app()
