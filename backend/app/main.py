from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware import CorrelationIdMiddleware
from app.services.events import channel, redis
from app.services.memory import close as close_memory


def setup_otel(app: FastAPI) -> None:
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        provider = TracerProvider(
            resource=Resource.create(
                {"service.name": settings.app_name, "deployment.environment": settings.environment}
            )
        )
        if settings.otel_exporter_endpoint:
            provider.add_span_processor(
                SimpleSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint))
            )
        else:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        # Telemetry must never prevent the control plane from starting.
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    yield
    await redis.aclose()
    await close_memory()


app = FastAPI(title=settings.app_name, version="1.1.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_otel(app)
app.include_router(api_router)


@app.get("/metrics")
async def metrics():
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health/live")
async def live():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready():
    await redis.ping()
    return {"status": "ready"}


@app.websocket("/ws/runs/{run_id}")
async def run_events(ws: WebSocket, run_id: UUID):
    await ws.accept()
    pub = redis.pubsub()
    await pub.subscribe(channel(run_id))
    try:
        while True:
            msg = await pub.get_message(ignore_subscribe_messages=True, timeout=30)
            if msg:
                await ws.send_text(msg["data"])
            else:
                await ws.send_json({"event": "HEARTBEAT"})
    except WebSocketDisconnect:
        pass
    finally:
        await pub.unsubscribe(channel(run_id))
        await pub.aclose()
