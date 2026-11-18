
"""
==========================================================
GANADOSALUD AI
API REST + RANDOM FOREST + PROMETHEUS

ACTIVIDAD 8
MONITORIZACIÓN, OBSERVABILIDAD Y SIMULACIÓN DE INCIDENTES
==========================================================

INC-001: Caída del backend (mediante Docker).
INC-002: Latencia elevada controlada.
INC-003: Error HTTP 500 cada N peticiones a /predict.

Las simulaciones son exclusivamente para pruebas académicas.
"""

# ========================================================
# IMPORTACIONES
# ========================================================

import os
import time
import threading

from pathlib import Path
from functools import lru_cache
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.monitoring import (
    monitoring_middleware,
    metrics_endpoint,
    PREDICTIONS,
)


# ========================================================
# CONFIGURACIÓN GENERAL
# ========================================================

MODEL_PATH = Path(__file__).with_name("model.joblib")


# ========================================================
# INC-002: SIMULACIÓN DE LATENCIA
# ========================================================

SIMULAR_LATENCIA = (
    os.getenv("SIMULAR_LATENCIA", "false").lower() == "true"
)

RETRASO_SEGUNDOS = float(
    os.getenv("RETRASO_SEGUNDOS", "1.5")
)

if RETRASO_SEGUNDOS < 0:
    raise ValueError(
        "RETRASO_SEGUNDOS no puede ser negativo"
    )


# ========================================================
# INC-003: SIMULACIÓN DE ERRORES HTTP 500
# ========================================================

SIMULAR_ERROR_500 = (
    os.getenv("SIMULAR_ERROR_500", "false").lower() == "true"
)

FRECUENCIA_ERROR = int(
    os.getenv("FRECUENCIA_ERROR", "5")
)

if FRECUENCIA_ERROR < 1:
    raise ValueError(
        "FRECUENCIA_ERROR debe ser mayor o igual a 1"
    )

# Contador de solicitudes a /predict.
# Se reinicia cuando se reinicia el proceso del backend.
contador_peticiones = 0

# Protege el contador frente a solicitudes concurrentes.
contador_lock = threading.Lock()


# ========================================================
# CREACIÓN DE LA APLICACIÓN FASTAPI
# ========================================================

app = FastAPI(
    title="GanadoSalud AI",
    version="1.0.0",
    description=(
        "Sistema educativo de inteligencia artificial para "
        "clasificar el estado de salud bovina mediante "
        "Random Forest. Incluye observabilidad con Prometheus "
        "y simulaciones controladas de incidentes."
    ),
)


# ========================================================
# CONFIGURACIÓN CORS
# ========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=["*"],
)


# ========================================================
# MONITORIZACIÓN CON PROMETHEUS
# ========================================================

# Registra las solicitudes HTTP y sus tiempos de respuesta.
app.middleware("http")(monitoring_middleware)

# Expone métricas para Prometheus.
app.add_api_route(
    "/metrics",
    metrics_endpoint,
    methods=["GET"],
    include_in_schema=False,
)


# ========================================================
# ESQUEMA DE DATOS DE ENTRADA
# ========================================================

class Entrada(BaseModel):

    animal_id: str = Field(
        min_length=1,
        max_length=80,
    )

    dia: int = Field(
        ge=1,
        le=366,
    )

    alimento_consumido_kg: float = Field(
        ge=0,
        le=100,
    )

    pasos_por_dia: int = Field(
        ge=0,
        le=100000,
    )

    horas_de_reposo: float = Field(
        ge=0,
        le=24,
    )

    temperatura_corp_c: float = Field(
        ge=30,
        le=45,
    )

    nivel_actividad: Literal[
        "Bajo",
        "Moderado",
        "Alto",
    ]


# ========================================================
# CARGA DEL MODELO RANDOM FOREST
# ========================================================

@lru_cache(maxsize=1)
def get_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Modelo no encontrado. Ejecute python train.py"
        )

    return joblib.load(MODEL_PATH)


# ========================================================
# ENDPOINT PRINCIPAL
# ========================================================

@app.get("/")
def home():

    return {
        "mensaje": "GanadoSalud AI API",
        "version": "1.0.0",
        "documentacion": "/docs",
        "estado": "/health",
        "monitorizacion": "/metrics",
    }


# ========================================================
# HEALTH CHECK
# ========================================================

@app.get("/health")
def health():

    try:
        model = get_model()

        return {
            "status": "ok",
            "modelo_cargado": bool(model),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Modelo no disponible: "
                f"{type(exc).__name__}"
            ),
        ) from exc


# ========================================================
# INFORMACIÓN DEL MODELO
# ========================================================

@app.get("/model/info")
def model_info():

    try:
        model = get_model()

        return {
            "algoritmo": "RandomForestClassifier",
            "clases": model.classes_.tolist(),
            "version": "1.0.0",
            "datos": "simulados",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible",
        ) from exc


# ========================================================
# ENDPOINT DE PREDICCIÓN
# ========================================================

@app.post("/predict")
def predict(payload: Entrada):

    global contador_peticiones

    try:

        # ================================================
        # INC-003: CONTADOR Y ERROR HTTP 500
        # ================================================

        if SIMULAR_ERROR_500:

            # La operación se protege para que no existan
            # incrementos simultáneos incorrectos.
            with contador_lock:
                contador_peticiones += 1
                numero_peticion = contador_peticiones

            # Cada quinta petición genera un error.
            if numero_peticion % FRECUENCIA_ERROR == 0:

                print(
                    f"[INC-003] Error HTTP 500 simulado "
                    f"en petición {numero_peticion}",
                    flush=True,
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "INC-003: Error interno simulado "
                        "para pruebas de monitorización."
                    ),
                )

        # ================================================
        # INC-002: SIMULACIÓN DE LATENCIA
        # ================================================

        if SIMULAR_LATENCIA:

            print(
                "[INC-002] Simulación de latencia "
                f"activada: {RETRASO_SEGUNDOS} segundos.",
                flush=True,
            )

            time.sleep(RETRASO_SEGUNDOS)

        # ================================================
        # CARGAR MODELO
        # ================================================

        model = get_model()

        # ================================================
        # PREPARAR DATOS
        # ================================================

        row = pd.DataFrame([
            {
                "Día": payload.dia,
                "Alimento_Consumido_kg":
                    payload.alimento_consumido_kg,
                "Pasos_por_día":
                    payload.pasos_por_dia,
                "Horas_de_Reposo":
                    payload.horas_de_reposo,
                "Temperatura_Corp_C":
                    payload.temperatura_corp_c,
                "Nivel_Actividad":
                    payload.nivel_actividad,
            }
        ])

        # ================================================
        # GENERAR PREDICCIÓN
        # ================================================

        prediction = str(
            model.predict(row)[0]
        )

        probabilities = model.predict_proba(row)[0]

        # ================================================
        # REGISTRAR PREDICCIÓN EXITOSA EN PROMETHEUS
        # ================================================

        PREDICTIONS.labels(
            diagnostico=prediction
        ).inc()

        # ================================================
        # DEVOLVER RESULTADO
        # ================================================

        return {
            "animal_id": payload.animal_id,
            "prediccion": prediction,
            "probabilidades": {
                str(clase): round(float(probabilidad), 4)
                for clase, probabilidad in zip(
                    model.classes_,
                    probabilities,
                )
            },
            "advertencia": (
                "Resultado educativo basado en datos "
                "simulados; no es diagnóstico veterinario."
            ),
        }

    # Mantener el código HTTP 500 simulado.
    except HTTPException:
        raise

    # Error específico cuando falta el modelo.
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
