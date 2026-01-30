# Desafio Técnico - Intuitive Care

Solução para o Teste de Entrada para Estagiários (v2.0).
O projeto consiste em um pipeline de dados (ETL) e uma interface web para análise de despesas de operadoras de saúde, utilizando dados públicos da ANS.

## Estrutura do Projeto

```text
├── data/              # Armazenamento local de dados (Raw/Processed)
├── docs/              # Documentação de decisões técnicas
├── src/
│   ├── 1_integration/    # Scripts de coleta (Scraping/Download)
│   ├── 2_transformation/ # Limpeza, validação e enriquecimento
│   ├── 3_database/       # Schema SQL e scripts de carga
│   └── 4_web/            # API (FastAPI) e Frontend (Vue.js)
├── requirements.txt
└── README.md
```

## Como Executar

### Pré-requisitos
* Python 3.8+
* Node.js (opcional, para rodar frontend localmente)

### Configuração
1. Instale as dependências Python:
   ```bash
   pip install -r requirements.txt
   ```

### Execução do Pipeline (ETL)
O pipeline deve ser executado sequencialmente:

1. **Extração:** Baixa e consolida os dados da ANS.
   ```bash
   python src/1_integration/main.py
   ```
2. **Transformação:** Enriquece com dados cadastrais e gera estatísticas.
   ```bash
   python src/2_transformation/main.py
   ```
3. **Carga no Banco:** Cria o banco SQLite e importa os dados.
   ```bash
   python src/3_database/import_data.py
   ```

### Execução da Aplicação Web
Inicie a API Backend:
```bash
cd src/4_web/backend
uvicorn main:app --reload
```
A API estará disponível em `http://localhost:8000/docs`.
