"""Entrena y guarda un pipeline reproducible con el CSV proporcionado."""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'dataset.csv'
MODEL = ROOT / 'app' / 'model.joblib'
METRICS = ROOT / 'metrics.json'
NUMERIC = ['Día', 'Alimento_Consumido_kg', 'Pasos_por_día', 'Horas_de_Reposo', 'Temperatura_Corp_C']
CATEGORICAL = ['Nivel_Actividad']
FEATURES = NUMERIC + CATEGORICAL
TARGET = 'Diagnóstico'

def train():
    df = pd.read_csv(DATA)
    missing = set(FEATURES + [TARGET]) - set(df.columns)
    if missing:
        raise ValueError(f'Columnas faltantes: {sorted(missing)}')
    # Animal_ID es un identificador, no una señal fisiológica; se excluye para evitar memorizar animales.
    x_train, x_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42, stratify=df[TARGET])
    preprocessor = ColumnTransformer([
        ('numeric', SimpleImputer(strategy='median'), NUMERIC),
        ('categorical', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore'))]), CATEGORICAL)
    ])
    pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', RandomForestClassifier(n_estimators=180, min_samples_leaf=3, random_state=42, n_jobs=-1, class_weight='balanced_subsample'))])
    pipeline.fit(x_train, y_train)
    pred = pipeline.predict(x_test)
    labels = sorted(df[TARGET].unique().tolist())
    metrics = {'filas': len(df), 'entrenamiento': len(x_train), 'prueba': len(x_test), 'features': FEATURES, 'clases': labels, 'accuracy': accuracy_score(y_test, pred), 'balanced_accuracy': balanced_accuracy_score(y_test, pred), 'classification_report': classification_report(y_test, pred, output_dict=True, zero_division=0), 'confusion_matrix': confusion_matrix(y_test, pred, labels=labels).tolist(), 'nota': 'Dataset simulado: métricas no equivalen a validación clínica.'}
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL)
    METRICS.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'accuracy': metrics['accuracy'], 'balanced_accuracy': metrics['balanced_accuracy'], 'modelo': str(MODEL)}, ensure_ascii=False))

if __name__ == '__main__':
    train()
