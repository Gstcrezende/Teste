from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from pathlib import Path
import pandas as pd

app = FastAPI(title="Intuitive Care Challenge API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "database.db"
DB_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DB_URL)

@app.get("/")
def read_root():
    return {"message": "API is running. Go to /docs for Swagger UI."}

@app.get("/api/operadoras")
def list_operadoras(page: int = 1, limit: int = 10, search: str = None):
    offset = (page - 1) * limit
    
    query_str = "SELECT * FROM operadoras"
    params = {}
    
    if search:
        query_str += " WHERE razao_social LIKE :search OR registro_ans LIKE :search"
        params['search'] = f"%{search}%"
        
    query_str += " LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = offset
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text(query_str), params)
            rows = result.mappings().all()
            return rows
        except Exception as e:
            # Fallback se tabela não existir
            return []

@app.get("/api/operadoras/{id}")
def get_operadora(id: str):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM operadoras WHERE registro_ans = :id"), {"id": id})
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Operadora not found")
        return row

@app.get("/api/operadoras/{id}/despesas")
def get_operadora_despesas(id: str):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM despesas_consolidadas WHERE registro_ans = :id"), {"id": id})
        rows = result.mappings().all()
        return rows

@app.get("/api/estatisticas")
def get_estatisticas():
    # Retorna dados já agregados da tabela (Cache pattern: pré-calculado na etapa 2/3)
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT * FROM despesas_agregadas LIMIT 100"))
            return result.mappings().all()
        except:
            return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
