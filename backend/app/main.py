from pathlib import Path
from functools import lru_cache
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

MODEL_PATH = Path(__file__).with_name('model.joblib')
app = FastAPI(title='DairyHealth AI', version='1.0.0', description='Clasificador educativo de salud bovina con datos simulados.')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'], allow_methods=['GET','POST'], allow_headers=['*'])

class Entrada(BaseModel):
    animal_id: str = Field(min_length=1, max_length=80)
    dia: int = Field(ge=1, le=366)
    alimento_consumido_kg: float = Field(ge=0, le=100)
    pasos_por_dia: int = Field(ge=0, le=100000)
    horas_de_reposo: float = Field(ge=0, le=24)
    temperatura_corp_c: float = Field(ge=30, le=45)
    nivel_actividad: Literal['Bajo', 'Moderado', 'Alto']

@lru_cache(maxsize=1)
def get_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError('Modelo no encontrado: ejecute python train.py')
    return joblib.load(MODEL_PATH)

@app.get('/')
def home():
    return {'mensaje': 'DairyHealth AI API', 'documentacion': '/docs'}

@app.get('/health')
def health():
    try:
        model = get_model()
        return {'status': 'ok', 'modelo_cargado': bool(model)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'Modelo no disponible: {type(exc).__name__}') from exc

@app.get('/model/info')
def model_info():
    try:
        model = get_model()
        return {'algoritmo': 'RandomForestClassifier', 'clases': model.classes_.tolist(), 'version': '1.0.0', 'datos': 'simulados'}
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Modelo no disponible') from exc

@app.post('/predict')
def predict(payload: Entrada):
    try:
        model = get_model()
        row = pd.DataFrame([{
            'Día': payload.dia, 'Alimento_Consumido_kg': payload.alimento_consumido_kg,
            'Pasos_por_día': payload.pasos_por_dia, 'Horas_de_Reposo': payload.horas_de_reposo,
            'Temperatura_Corp_C': payload.temperatura_corp_c, 'Nivel_Actividad': payload.nivel_actividad
        }])
        prediction = str(model.predict(row)[0])
        probabilities = model.predict_proba(row)[0]
        return {'animal_id': payload.animal_id, 'prediccion': prediction, 'probabilidades': {str(k): round(float(v), 4) for k, v in zip(model.classes_, probabilities)}, 'advertencia': 'Resultado educativo basado en datos simulados; no es diagnóstico veterinario.'}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
