# GanadoSalud AI — detección educativa de alteraciones de salud bovina

Aplicación React + FastAPI + Random Forest, construida con el dataset **FaseII_Simulados.csv** (30 000 registros simulados). Las predicciones no constituyen diagnóstico veterinario.

## Requisitos
- Docker Desktop / Docker Engine con Compose v2 (recomendado 4 GB RAM disponibles)
- Para ejecución sin Docker: Python 3.11, Node.js 22 y npm

## Inicio rápido con Docker
```bash
docker compose up --build -d
docker compose ps
docker compose logs -f backend
```
- Interfaz: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

El Dockerfile del backend **entrena el modelo durante la construcción de la imagen** con el CSV incluido y guarda `app/model.joblib`. Esto permite reproducir el modelo sin adjuntar binarios. La construcción puede tardar varios minutos.

## Entrenamiento y pruebas fuera de Docker
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt pytest httpx
python train.py
python -m pytest -q
uvicorn app.main:app --reload
```

## Prueba de inferencia
```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"animal_id":"VACA_1","dia":10,"alimento_consumido_kg":20,"pasos_por_dia":2500,"horas_de_reposo":7,"temperatura_corp_c":38.5,"nivel_actividad":"Moderado"}'
```

## Endpoints
- `GET /` información del servicio.
- `GET /health` salud y carga del modelo.
- `GET /model/info` clases y algoritmo.
- `POST /predict` inferencia con validación de tipos/rangos; devuelve clase y probabilidades.
- `GET /docs` OpenAPI/Swagger.

## Arquitectura
Navegador → Nginx/React (puerto 3000) → proxy `/api` → FastAPI (puerto 8000) → pipeline scikit-learn. El backend expone el puerto 8000 para pruebas locales; en producción conviene mantenerlo privado.

## Documentación
- `docs/despliegue_nube.md`
- `docs/validacion.md`
- `docs/arquitectura.md`

## Seguridad y limitaciones
- Dataset sintético, no validado en animales reales.
- `Animal_ID` se utiliza para identificar la respuesta, no para entrenar.
- El modelo usa división estratificada 80/20 con semilla 42; la métrica de test no implica utilidad clínica.
- `joblib` deserializa código: cargar únicamente artefactos propios o de confianza.
