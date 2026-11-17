"""
GanadoSalud AI
Actividad 8 - Detección de Data Drift con Evidently AI

Compara los datos de referencia con datos simulados
que presentan cambios en sus distribuciones.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd

from evidently import Report
from evidently.presets import DataDriftPreset


# ==========================================
# CONFIGURACIÓN
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / "backend" / "dataset.csv"

RESULTADOS = ROOT / "monitoring" / "resultados"

RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

FEATURES = [
    "Día",
    "Alimento_Consumido_kg",
    "Pasos_por_día",
    "Horas_de_Reposo",
    "Temperatura_Corp_C",
    "Nivel_Actividad"
]


# ==========================================
# CARGAR DATASET
# ==========================================

print("Cargando dataset original...")

df = pd.read_csv(DATASET)

faltantes = set(FEATURES) - set(df.columns)

if faltantes:
    raise ValueError(
        f"Faltan columnas: {sorted(faltantes)}"
    )

# Datos de referencia
reference = df[FEATURES].copy()

# Datos actuales simulados
current = reference.copy()


# ==========================================
# SIMULAR DATA DRIFT
# ==========================================

print("Simulando cambios en los datos...")

rng = np.random.default_rng(42)

# Aumentar temperaturas
current["Temperatura_Corp_C"] = (
    current["Temperatura_Corp_C"] + 1.5
)

# Reducir consumo de alimento
current["Alimento_Consumido_kg"] = (
    current["Alimento_Consumido_kg"] * 0.65
)

# Reducir actividad física
current["Pasos_por_día"] = (
    current["Pasos_por_día"] * 0.45
)

# Incrementar horas de reposo
current["Horas_de_Reposo"] = (
    current["Horas_de_Reposo"] + 2
)

# Cambiar distribución del nivel de actividad
current["Nivel_Actividad"] = rng.choice(
    ["Bajo", "Moderado", "Alto"],
    size=len(current),
    p=[0.85, 0.10, 0.05]
)


# ==========================================
# GENERAR REPORTE EVIDENTLY
# ==========================================

print("Analizando data drift...")

report = Report([
    DataDriftPreset()
])

snapshot = report.run(
    reference_data=reference,
    current_data=current
)


# ==========================================
# GUARDAR RESULTADOS
# ==========================================

ruta_html = RESULTADOS / "reporte_data_drift.html"

ruta_json = RESULTADOS / "reporte_data_drift.json"

snapshot.save_html(str(ruta_html))

snapshot.save_json(str(ruta_json))

# Guardar datos simulados
ruta_csv = RESULTADOS / "datos_simulados.csv"

current.to_csv(
    ruta_csv,
    index=False
)

print("\nAnálisis finalizado.")

print(f"Reporte HTML: {ruta_html}")

print(f"Reporte JSON: {ruta_json}")

print(f"Datos simulados: {ruta_csv}")