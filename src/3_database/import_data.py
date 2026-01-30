import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import logging
import sys

# Configuração
logging.basicConfig(level=logging.INFO)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# String de Conexão (Padrão SQLite para teste local, altere para MySQL/Postgres em produção)
# Exemplo MySQL: "mysql+mysqlconnector://user:pass@localhost/db_name"
DB_URL = "sqlite:///" + str(BASE_DIR / "database.db")

def import_data():
    if not DATA_PROCESSED.exists():
        logging.error("Diretório de dados processados não encontrado.")
        return

    engine = create_engine(DB_URL)
    
    # 1. Carregar CSVs
    try:
        df_consol = pd.read_csv(DATA_PROCESSED / "consolidado_despesas.csv", sep=';')
        df_agreg = pd.read_csv(DATA_PROCESSED / "despesas_agregadas.csv", sep=';')
        # Para operadoras, vamos deduzir do consolidado se não tivermos o arquivo separado limpo
        # ou usar as colunas disponíveis.
        
        logging.info("CSVs carregados.")
    except Exception as e:
        logging.error(f"Erro ao ler CSVs: {e}")
        return

    # 2. Criar Tabelas (Executando schema.sql - Adaptado para SQLite/SQLAlchemy)
    # Nota: Em produção, usar migration tools (Alembic). Aqui faremos via Pandas/SQLAlchemy simples.
    
    # Simular Operadoras (Extraindo únicos do consolidado + agregado)
    # No mundo real, carregariamos o CSV de cadastro completo da etapa 2
    operadoras = df_consol[['CNPJ', 'RazaoSocial']].drop_duplicates().rename(columns={
        'CNPJ': 'registro_ans', # Assumindo mapeamento feito na etapa 1
        'RazaoSocial': 'razao_social'
    })
    # Adicionar UF do agregado se possível
    if 'UF' in df_agreg.columns:
        ops_uf = df_agreg[['RazaoSocial', 'UF']].drop_duplicates()
        operadoras = pd.merge(operadoras, ops_uf, left_on='razao_social', right_on='RazaoSocial', how='left').drop(columns=['RazaoSocial'])

    logging.info("Importando Operadoras...")
    operadoras.to_sql('operadoras', engine, if_exists='replace', index=False)

    logging.info("Importando Despesas Consolidadas...")
    # Ajuste colunas para bater com o schema
    despesas = df_consol.rename(columns={
        'CNPJ': 'registro_ans',
        'Ano': 'ano', 
        'Trimestre': 'trimestre',
        'ValorDespesas': 'valor_despesas'
    })
    despesas[['registro_ans', 'ano', 'trimestre', 'valor_despesas']].to_sql('despesas_consolidadas', engine, if_exists='replace', index=False)

    logging.info("Importando Despesas Agregadas...")
    agregadas = df_agreg.rename(columns={
        'RazaoSocial': 'razao_social',
        'UF': 'uf',
        'TotalDespesas': 'total_despesas',
        'MediaTrimestral': 'media_trimestral',
        'DesvioPadrao': 'desvio_padrao'
    })
    agregadas.to_sql('despesas_agregadas', engine, if_exists='replace', index=False)

    logging.info("Importação concluída com sucesso!")

if __name__ == "__main__":
    import_data()
