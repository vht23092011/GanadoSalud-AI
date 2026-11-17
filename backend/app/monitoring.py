"""
GanadoSalud AI
Monitorización de métricas mediante Prometheus.
"""

import time

from fastapi import Request
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from starlette.responses import Response


REQUESTS = Counter(
    "gs_requests_total",
    "Total de solicitudes HTTP",
    ["method", "endpoint", "status"]
)

LATENCY = Histogram(
    "gs_request_duration_seconds",
    "Duracion de las solicitudes HTTP",
    ["method", "endpoint"],
    buckets=(
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1,
        2.5,
        5,
        10,
        float("inf")
    )
)

PREDICTIONS = Counter(
    "gs_predictions_total",
    "Total de predicciones realizadas",
    ["diagnostico"]
)

HTTP_ERRORS = Counter(
    "gs_http_errors_total",
    "Total de errores HTTP",
    ["method", "endpoint", "status"]
)


async def monitoring_middleware(request: Request, call_next):

    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        status_code = response.status_code

    except Exception:
        status_code = 500
        raise

    finally:
        duration = time.perf_counter() - start_time

        route = request.scope.get("route")
        endpoint = route.path if route else request.url.path

        REQUESTS.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        if status_code >= 400:
            HTTP_ERRORS.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()

    return response


def metrics_endpoint():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )