"""
GanadoSalud AI
Entrenamiento y seguimiento del modelo con MLflow.

Modelo: Random Forest Classifier
Actividad 8: Monitorización y Observabilidad
"""

from pathlib import Path
import json
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix
)

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ==================================================
# CONFIGURACIÓN
# ==================================================

ROOT = Path(__file__).resolve().parent

DATA = ROOT / "dataset.csv"

MODEL = ROOT / "app" / "model.joblib"

METRICS = ROOT / "metrics.json"

NUMERIC = [
    "Día",
    "Alimento_Consumido_kg",
    "Pasos_por_día",
    "Horas_de_Reposo",
    "Temperatura_Corp_C"
]

CATEGORICAL = [
    "Nivel_Actividad"
]

FEATURES = NUMERIC + CATEGORICAL

TARGET = "Diagnóstico"


# ==================================================
# CONFIGURACIÓN MLFLOW
# ==================================================

# Almacenar los experimentos localmente
MLFLOW_DIR = ROOT / "mlruns"

MLFLOW_DIR.mkdir(exist_ok=True)

mlflow.set_tracking_uri(MLFLOW_DIR.as_uri())

# Nombre del experimento
mlflow.set_experiment("GanadoSalud_AI")


# ==================================================
# ENTRENAMIENTO
# ==================================================

def train():

    print("Iniciando entrenamiento GanadoSalud AI...")

    # Cargar dataset
    df = pd.read_csv(DATA)

    missing = set(FEATURES + [TARGET]) - set(df.columns)

    if missing:
        raise ValueError(
            f"Columnas faltantes: {sorted(missing)}"
        )

    # Separación entrenamiento / prueba
    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES],
        df[TARGET],
        test_size=0.2,
        random_state=42,
        stratify=df[TARGET]
    )

    # Preprocesamiento
    preprocessor = ColumnTransformer([
        (
            "numeric",
            SimpleImputer(strategy="median"),
            NUMERIC
        ),
        (
            "categorical",
            Pipeline([
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    )
                ),
                (
                    "onehot",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    )
                )
            ]),
            CATEGORICAL
        )
    ])

    # Modelo Random Forest
    pipeline = Pipeline([
        (
            "preprocessor",
            preprocessor
        ),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=180,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
                class_weight="balanced_subsample"
            )
        )
    ])

    # ==================================================
    # EXPERIMENTO MLFLOW
    # ==================================================

    with mlflow.start_run(
        run_name="RandomForest_GanadoSalud"
    ):

        # Registrar parámetros
        mlflow.log_param(
            "modelo",
            "RandomForestClassifier"
        )

        mlflow.log_param(
            "n_estimators",
            180
        )

        mlflow.log_param(
            "min_samples_leaf",
            3
        )

        mlflow.log_param(
            "test_size",
            0.2
        )

        mlflow.log_param(
            "random_state",
            42
        )

        mlflow.log_param(
            "dataset_rows",
            len(df)
        )

        # Entrenar
        print("Entrenando modelo...")

        pipeline.fit(
            x_train,
            y_train
        )

        # Predicciones
        pred = pipeline.predict(x_test)

        labels = sorted(
            df[TARGET].unique().tolist()
        )

        # Métricas
        accuracy = accuracy_score(
            y_test,
            pred
        )

        balanced_accuracy = balanced_accuracy_score(
            y_test,
            pred
        )

        report = classification_report(
            y_test,
            pred,
            output_dict=True,
            zero_division=0
        )

        matrix = confusion_matrix(
            y_test,
            pred,
            labels=labels
        )

        # Registrar métricas en MLflow
        mlflow.log_metric(
            "accuracy",
            accuracy
        )

        mlflow.log_metric(
            "balanced_accuracy",
            balanced_accuracy
        )

        mlflow.log_metric(
            "precision_weighted",
            report["weighted avg"]["precision"]
        )

        mlflow.log_metric(
            "recall_weighted",
            report["weighted avg"]["recall"]
        )

        mlflow.log_metric(
            "f1_weighted",
            report["weighted avg"]["f1-score"]
        )

        # Métricas por clase
        for label in labels:

            mlflow.log_metric(
                f"precision_{label}",
                report[label]["precision"]
            )

            mlflow.log_metric(
                f"recall_{label}",
                report[label]["recall"]
            )

            mlflow.log_metric(
                f"f1_{label}",
                report[label]["f1-score"]
            )

        # Diccionario de resultados
        metrics = {
            "filas": len(df),
            "entrenamiento": len(x_train),
            "prueba": len(x_test),
            "features": FEATURES,
            "clases": labels,
            "accuracy": accuracy,
            "balanced_accuracy": balanced_accuracy,
            "classification_report": report,
            "confusion_matrix": matrix.tolist(),
            "nota": (
                "Dataset simulado: métricas no "
                "equivalen a validación clínica."
            )
        }

        # Guardar modelo original
        MODEL.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        joblib.dump(
            pipeline,
            MODEL
        )

        # Guardar métricas JSON
        METRICS.write_text(
            json.dumps(
                metrics,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        # Registrar archivos en MLflow
        mlflow.log_artifact(str(METRICS))
        mlflow.log_artifact(str(MODEL))

        # Registrar pipeline completo
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            name="modelo_ganadosalud"
        )

        # Resultados
        print("\nEntrenamiento finalizado.")

        print(
            f"Accuracy: {accuracy:.4f}"
        )

        print(
            f"Balanced Accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            "\nExperimento registrado en MLflow."
        )

        print(
            f"Modelo guardado en: {MODEL}"
        )


if __name__ == "__main__":
    train()