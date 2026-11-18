
"""
GANADOSALUD AI - ACTIVIDAD 8
AutoRecovery dockerizado.

Supervisa el backend y ejecuta una recuperación
automática después de tres fallos consecutivos.

Diseñado exclusivamente para laboratorio local.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import docker
import requests


# ==========================================
# CONFIGURACIÓN
# ==========================================

HEALTH_URL = os.getenv(
    "HEALTH_URL",
    "http://backend:8000/health"
)

PROJECT_NAME = os.getenv(
    "COMPOSE_PROJECT_NAME",
    "ganadosaludai"
)

INTERVALO = 5
MAX_FALLOS = 3
MAX_VERIFICACIONES = 12

LOG_PATH = Path(
    "/app/resultados/auto_recovery.jsonl"
)

cliente = docker.from_env()


# ==========================================
# REGISTRAR EVENTOS
# ==========================================

def registrar(evento, detalle):

    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    registro = {
        "fecha": datetime.now(
            timezone.utc
        ).isoformat(),
        "evento": evento,
        "detalle": detalle
    }

    with LOG_PATH.open(
        "a",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            json.dumps(
                registro,
                ensure_ascii=False
            ) + "\n"
        )

    print(
        f"[{evento}] {detalle}",
        flush=True
    )


# ==========================================
# VERIFICAR API
# ==========================================

def verificar_api():

    try:

        respuesta = requests.get(
            HEALTH_URL,
            timeout=3
        )

        if respuesta.status_code != 200:
            return False

        datos = respuesta.json()

        return (
            datos.get("status") == "ok"
            and datos.get("modelo_cargado") is True
        )

    except (
        requests.RequestException,
        ValueError
    ):
        return False


# ==========================================
# LOCALIZAR CONTENEDOR
# ==========================================

def obtener_backend():

    contenedores = cliente.containers.list(
        all=True,
        filters={
            "label": [
                f"com.docker.compose.project={PROJECT_NAME}",
                "com.docker.compose.service=backend"
            ]
        }
    )

    if len(contenedores) != 1:

        registrar(
            "ERROR_CONTENEDOR",
            "No se encontró un backend único"
        )

        return None

    return contenedores[0]


# ==========================================
# EJECUTAR RECUPERACIÓN
# ==========================================

def recuperar_backend():

    registrar(
        "RECUPERACION_INICIADA",
        "Iniciando recuperación automática"
    )

    try:

        backend = obtener_backend()

        if backend is None:
            return False

        backend.reload()

        if backend.status in (
            "exited",
            "created"
        ):

            backend.start()

            registrar(
                "CONTENEDOR_INICIADO",
                "Docker inició el backend detenido"
            )

        elif backend.status == "running":

            backend.restart(timeout=10)

            registrar(
                "CONTENEDOR_REINICIADO",
                "Docker reinició el backend"
            )

        else:

            registrar(
                "ESTADO_NO_ADMITIDO",
                f"Estado del backend: {backend.status}"
            )

            return False

        return True

    except docker.errors.DockerException as error:

        registrar(
            "ERROR_RECUPERACION",
            str(error)
        )

        return False


# ==========================================
# VALIDAR RECUPERACIÓN
# ==========================================

def validar_recuperacion():

    for intento in range(
        1,
        MAX_VERIFICACIONES + 1
    ):

        time.sleep(INTERVALO)

        if verificar_api():

            registrar(
                "SERVICIO_RECUPERADO",
                "HTTP 200 y modelo cargado correctamente"
            )

            return True

        registrar(
            "VERIFICACION",
            f"Intento {intento}: servicio no disponible"
        )

    registrar(
        "RECUPERACION_NO_CONFIRMADA",
        "Se requiere intervención manual"
    )

    return False


# ==========================================
# MONITORIZACIÓN AUTOMÁTICA
# ==========================================

def iniciar():

    fallos = 0

    registrar(
        "MONITORIZACION_INICIADA",
        "AutoRecovery iniciado desde Docker"
    )

    while True:

        if verificar_api():

            if fallos > 0:

                registrar(
                    "SERVICIO_RESTABLECIDO",
                    "La API volvió a responder"
                )

            fallos = 0

            print(
                "[OK] Backend disponible",
                flush=True
            )

        else:

            fallos += 1

            registrar(
                "FALLO_DETECTADO",
                f"Fallo {fallos}/{MAX_FALLOS}"
            )

            if fallos >= MAX_FALLOS:

                registrar(
                    "INCIDENTE_CONFIRMADO",
                    "INC-004: Backend no disponible"
                )

                if recuperar_backend():

                    if validar_recuperacion():
                        fallos = 0
                        continue

                registrar(
                    "INTERVENCION_MANUAL_REQUERIDA",
                    "Se detiene la automatización para evitar "
                    "reinicios repetidos"
                )

                break

        time.sleep(INTERVALO)


if __name__ == "__main__":

    try:
        iniciar()

    except KeyboardInterrupt:

        registrar(
            "MONITORIZACION_DETENIDA",
            "Detención manual"
        )

    except docker.errors.DockerException as error:

        registrar(
            "ERROR_DOCKER",
            str(error)
        )
