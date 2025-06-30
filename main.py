from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import engine, Base
from routers import (
    categories,
    documents,
    emails,
    ai,
    auto_reply,
    mailbox,
    analytics,
    logs,
    user,
    moniter,
)
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


sentry_sdk.init(
    dsn=os.getenv(
        "SENTRY_DSN",
        "https://d31daf5b6208594032d288b202a43101@o4509439020302336.ingest.us.sentry.io/4509588050477056",
    ),
    send_default_pii=True,
    integrations=[
        StarletteIntegration(
            transaction_style="url",
            failed_request_status_codes={400, *range(500, 599)},
            http_methods_to_capture=(
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
            ),
        ),
        FastApiIntegration(
            transaction_style="url",
            failed_request_status_codes={400, *range(500, 599)},
            http_methods_to_capture=(
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
            ),
        ),
    ],
    environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
)

print(
    "Sentry initialized with environment:",
    os.getenv("SENTRY_ENVIRONMENT", "development"),
)

app = FastAPI(
    title="Smart Email Auto-Responder API",
    description="AI-powered email auto-responder with intelligent categorization and response generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": str(exc) if app.debug else None,
            },
        },
    )


# Include routers
app.include_router(user.router, prefix="/v1")
app.include_router(categories.router, prefix="/v1")
app.include_router(documents.router, prefix="/v1")
app.include_router(emails.router, prefix="/v1")
app.include_router(ai.router, prefix="/v1")
app.include_router(auto_reply.router, prefix="/v1")
app.include_router(mailbox.router, prefix="/v1")
app.include_router(analytics.router, prefix="/v1")
app.include_router(logs.router, prefix="/v1")
app.include_router(moniter.router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "AI Email Auto-Responder API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/sentry-debug")
async def trigger_error():
    return 1 / 0
