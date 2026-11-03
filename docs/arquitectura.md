# Arquitectura técnica

## Componentes
1. **React/Vite**: captura y visualización de los resultados.
2. **Nginx**: sirve archivos estáticos y redirige `/api/` a `backend:8000/` dentro de la red Compose.
3. **FastAPI**: valida entradas con Pydantic y responde con JSON; Swagger en `/docs`.
4. **Pipeline sklearn**: imputación de numéricas, imputación y one-hot para actividad, RandomForest multiclase.
5. **Docker Compose**: levanta servicios aislados con nombres DNS internos.

## Flujo
`Usuario → React → /api/predict → Nginx → FastAPI /predict → modelo.joblib → JSON → React`

## Datos y decisión de diseño
- Fuente: `backend/dataset.csv`, 30 000 filas, 8 columnas.
- Etiqueta: `Diagnóstico` (`Sano`, `Observación`, `Enfermo`).
- Características: Día, alimento, pasos, reposo, temperatura, actividad.
- `Animal_ID` no se usa como predictor para reducir aprendizaje espurio de identificadores.
- Los datos están desbalanceados; se reportan exactitud, balanced accuracy y métricas por clase.

## Portabilidad
Imágenes Linux basadas en Python 3.11 y Node 22 / Nginx. Los comandos Compose son iguales en macOS, Windows y Linux con Docker instalado.
