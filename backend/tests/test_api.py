from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
VALID = {'animal_id':'VACA_1','dia':10,'alimento_consumido_kg':20,'pasos_por_dia':2500,'horas_de_reposo':7,'temperatura_corp_c':38.5,'nivel_actividad':'Moderado'}

def test_health():
    assert client.get('/health').status_code == 200

def test_predict():
    response = client.post('/predict', json=VALID)
    assert response.status_code == 200
    data = response.json()
    assert data['prediccion'] in {'Sano', 'Observación', 'Enfermo'}
    assert abs(sum(data['probabilidades'].values()) - 1) < 0.001

def test_invalid_temperature():
    assert client.post('/predict', json={**VALID, 'temperatura_corp_c': -1}).status_code == 422

def test_missing_field():
    p = dict(VALID)
    del p['dia']
    assert client.post('/predict', json=p).status_code == 422

def test_invalid_category():
    assert client.post('/predict', json={**VALID, 'nivel_actividad':'Extremo'}).status_code == 422

def test_boundary_values():
    response = client.post('/predict', json={**VALID, 'pasos_por_dia':0, 'horas_de_reposo':24, 'alimento_consumido_kg':0})
    assert response.status_code == 200
