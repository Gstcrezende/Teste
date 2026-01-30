# Decisões Técnicas e Arquitetura

Este documento descreve as escolhas técnicas adotadas durante o desenvolvimento do teste prático.

## Backend e Integração

### Python
Optei por Python devido à facilidade de manipulação de dados com Pandas e `zipfile`. Para o processamento dos dados da ANS, que embora volumosos não chegam a ser Big Data (GBs), o Pandas em memória foi suficiente e mais rápido de implementar que uma solução baseada em streaming ou Spark.

### Web Framework: FastAPI
Escolhi FastAPI ao invés de Flask por dois motivos principais:
1. **Performance Async**: Melhor para I/O operations se escalarmos para muitas requests.
2. **Produtividade**: A validação automática com Pydantic e a geração automática do Swagger (docs) economizaram tempo na criação da documentação da API.

### Banco de Dados
Para o teste, configurei o projeto para rodar com **SQLite** para facilitar a execução local sem necessidade de subir containers Docker ou instalar MySQL/Postgres.
No entanto, o uso de ORM (SQLAlchemy) e SQL padrão permite migrar para PostgreSQL apenas alterando a string de conexão.

A modelagem seguiu uma abordagem híbrida:
- `operadoras` e `despesas_consolidadas` estão normalizadas (3NF) para integridade.
- `despesas_agregadas` funciona como uma tabela de leitura rápida (read model), pré-processada na etapa de ETL.

## Desafios na Integração ANS

Durante a extração dos dados (Etapa 1), notei que a estrutura dos arquivos no servidor da ANS varia entre trimestres. Em 2025, os arquivos CSV parecem ter sido unificados, diferente da descrição inicial que sugeria múltiplos arquivos.

Para contornar isso, implementei uma busca flexível: o script localiza o arquivo CSV principal dentro do ZIP e filtra as linhas baseadas no `CD_CONTA_CONTABIL` (iniciados em '4' para despesas) e na descrição ("EVENTOS"/"SINISTROS").

Na etapa de enriquecimento, o link entre os dados contábeis (chave `REG_ANS`) e o cadastro de operadoras (chave `Registro_ANS`) foi feito via join. Algumas operadoras listadas no contábil não foram encontradas no cadastro ativo baixado, sendo tratadas como "Operadora Desconhecida" para manter a integridade dos valores financeiros.

## Frontend
Utilizei Vue.js 3 com Composition API. A interface é simples, focada em mostrar a visualização dos dados processados.
