from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running. Go to /docs for Swagger UI."}

def test_list_operadoras():
    response = client.get("/api/operadoras")
    # Mesmo sem banco, deve retornar 200 (lista vazia ou erro tratado) 
    # ou 500 se o banco não existir. 
    # O código atual retorna [] no except, então deve ser 200.
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_estatisticas():
    response = client.get("/api/estatisticas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
