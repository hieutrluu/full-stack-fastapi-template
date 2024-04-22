import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
import logging

# Add inngest for event driven architecture
import inngest
import inngest.fast_api
# Create an Inngest client
inngest_client = inngest.Inngest(
    app_id="fast_api_example",
    logger=logging.getLogger("uvicorn"),
)


# Create an Inngest function
@inngest_client.create_function(
    fn_id="my_function",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="app/my_function"),
)
async def my_function(ctx: inngest.Context, step: inngest.Step) -> str:
    ctx.logger.info(ctx.event)
    return "done"


def custom_generate_unique_id(route: APIRoute) -> str:
    # return f"{route.tags[0]}-{route.name}"
    return f"{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

inngest.fast_api.serve(app, inngest_client, [my_function])
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
