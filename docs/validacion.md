# Documento de validación y pruebas

## Objetivo
Verificar carga del modelo, predicción, validación de entradas, comunicación frontend-backend y funcionamiento de contenedores.

## Casos automatizados
| Caso | Entrada / acción | Resultado esperado |
|---|---|---|
| CP-01 | GET `/health` | HTTP 200, modelo cargado |
| CP-02 | POST `/predict` válido | HTTP 200, clase y probabilidades |
| CP-03 | Temperatura -1 | HTTP 422 |
| CP-04 | Falta `dia` | HTTP 422 |
| CP-05 | Actividad `Extremo` | HTTP 422 |
| CP-06 | Pasos 0, reposo 24, alimento 0 | HTTP 200: límites permitidos por esquema |

## Pruebas manuales pendientes
| Caso | Acción | Evidencia |
|---|---|---|
| CP-07 | `docker compose build` | Captura de imagen construida |
| CP-08 | `docker compose up -d` | `docker compose ps` |
| CP-09 | Abrir `localhost:3000` y predecir | Captura del frontend |
| CP-10 | Abrir `/docs` | Captura Swagger |
| CP-11 | Detener backend y enviar formulario | Mensaje de error controlado |

## Ejecución
```bash
cd backend
python train.py
python -m pytest -q
```
Instalar antes: `pip install -r requirements.txt pytest httpx`.

## Resultados
Consultar `backend/metrics.json` para métricas del conjunto de prueba. Registrar las salidas de Pytest y Docker tras ejecutar en el equipo destino; no presentar resultados esperados como evidencias observadas.

## Conclusiones y límites
La validación técnica no prueba eficacia clínica. Los datos simulados y el desbalance de clases limitan la generalización. Se requiere validación veterinaria y datos reales antes de cualquier uso operativo.
