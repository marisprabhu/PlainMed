"""FastAPI application factory.

Serves the mobile web app and the JSON API from one process. Every response
carries no-store headers, and the PHI log filter is installed before any
route can run.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from plainmed import __version__
from plainmed.api.retention import NO_STORE_HEADERS, install_phi_log_filter
from plainmed.api.routes import router
from plainmed.api.runtime import Runtime
from plainmed.api.security import RateLimiter
from plainmed.config import AppConfig

MOBILE_DIR = Path(__file__).resolve().parents[3] / "app" / "mobile"

# Uploads above this are rejected before the body is read, so a large file
# cannot exhaust memory on a worker.
MAX_BODY_BYTES = 13 * 1024 * 1024


def create_app(config: AppConfig | None = None, warmup: bool = True) -> FastAPI:
    config = config or AppConfig()
    install_phi_log_filter(("uvicorn.access", "uvicorn.error", "fastapi"))
    logging.basicConfig(
        level=os.environ.get("PLAINMED_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    runtime = Runtime(config)
    limiter = RateLimiter(
        rate_per_minute=int(os.environ.get("PLAINMED_RATE_PER_MIN", "20")),
        burst=int(os.environ.get("PLAINMED_RATE_BURST", "10")),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if warmup:
            runtime.warmup()
        yield

    app = FastAPI(
        title="PlainMed API",
        version=__version__,
        description=(
            "Explains medical reports in plain language with source links. "
            "Reports are processed in memory and never stored."
        ),
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.state.runtime = runtime
    app.state.limiter = limiter

    @app.middleware("http")
    async def guard_and_harden(request: Request, call_next):
        length = request.headers.get("content-length")
        if length is not None:
            try:
                if int(length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "detail": "That file is too large. Try a smaller photo.",
                        },
                        headers=dict(NO_STORE_HEADERS),
                    )
            except ValueError:
                pass

        response = await call_next(request)
        for key, value in NO_STORE_HEADERS.items():
            response.headers[key] = value
        return response

    app.include_router(router, prefix="/api/v1")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        """Browsers request this regardless of the <link rel="icon"> tag.

        Serving the SVG here stops a 404 appearing in the log, which during
        a demo invites a question that has nothing to do with the product.
        """
        icon = MOBILE_DIR / "logo.svg"
        if icon.is_file():
            return FileResponse(str(icon), media_type="image/svg+xml")
        return JSONResponse(status_code=404, content={"detail": "no icon"})

    if MOBILE_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=str(MOBILE_DIR), html=True), name="mobile"
        )

    return app


app = create_app()
