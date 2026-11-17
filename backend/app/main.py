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
    PREDICTIONS
)


MODEL_PATH = Path(__file__).with_name("model.joblib")

app = FastAPI(
    title="GanadoSalud AI",
    version="1.0.0",
    description=(
        "Clasificador educativo de salud bovina "
        "con monitorizacion mediante Prometheus."
    )
)


# ==========================================
# CONFIGURACION CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)


# ==========================================
# MONITORIZACION PROMETHEUS
# ==========================================

app.middleware("http")(monitoring_middleware)

app.add_api_route(
    "/metrics",
    metrics_endpoint,
    methods=["GET"],
    include_in_schema=False
)


# ==========================================
# MODELO DE ENTRADA
# ==========================================

class Entrada(BaseModel):

    animal_id: str = Field(
        min_length=1,
        max_length=80
    )

    dia: int = Field(
        ge=1,
        le=366
    )

    alimento_consumido_kg: float = Field(
        ge=0,
        le=100
    )

    pasos_por_dia: int = Field(
        ge=0,
        le=100000
    )

    horas_de_reposo: float = Field(
        ge=0,
        le=24
    )

    temperatura_corp_c: float = Field(
        ge=30,
        le=45
    )

    nivel_actividad: Literal[
        "Bajo",
        "Moderado",
        "Alto"
    ]


# ==========================================
# CARGAR MODELO RANDOM FOREST
# ==========================================

@lru_cache(maxsize=1)
def get_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Modelo no encontrado: ejecute python train.py"
        )

    return joblib.load(MODEL_PATH)


# ==========================================
# ENDPOINT PRINCIPAL
# ==========================================

@app.get("/")
def home():

    return {
        "mensaje": "GanadoSalud AI API",
        "documentacion": "/docs",
        "monitorizacion": "/metrics"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    try:
        model = get_model()

        return {
            "status": "ok",
            "modelo_cargado": bool(model)
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "Modelo no disponible: "
                f"{type(exc).__name__}"
            )
        ) from exc


# ==========================================
# INFORMACION DEL MODELO
# ==========================================

@app.get("/model/info")
def model_info():

    try:
        model = get_model()

        return {
            "algoritmo": "RandomForestClassifier",
            "clases": model.classes_.tolist(),
            "version": "1.0.0",
            "datos": "simulados"
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible"
        ) from exc


# ==========================================
# PREDICCION DEL MODELO
# ==========================================

@app.post("/predict")
def predict(payload: Entrada):

    try:

        model = get_model()

        row = pd.DataFrame([{

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
                payload.nivel_actividad

        }])

        # Prediccion real Random Forest
        prediction = str(
            model.predict(row)[0]
        )

        probabilities = model.predict_proba(row)[0]

        # Registrar prediccion en Prometheus
        PREDICTIONS.labels(
            diagnostico=prediction
        ).inc()

        return {

            "animal_id": payload.animal_id,

            "prediccion": prediction,

            "probabilidades": {

                str(k): round(float(v), 4)

                for k, v in zip(
                    model.classes_,
                    probabilities
                )

            },

            "advertencia": (
                "Resultado educativo basado en datos "
                "simulados; no es diagnóstico veterinario."
            )

        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc)
        ) from exc