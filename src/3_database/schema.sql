-- Tabela de Operadoras (Dados Cadastrais)
CREATE TABLE IF NOT EXISTS operadoras (
    registro_ans VARCHAR(20) PRIMARY KEY,
    cnpj VARCHAR(20),
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Despesas Consolidadas (Normalizada)
-- Trade-off: Normalização para reduzir redundância de dados cadastrais
CREATE TABLE IF NOT EXISTS despesas_consolidadas (
    id SERIAL PRIMARY KEY, -- Usar AUTO_INCREMENT no MySQL
    registro_ans VARCHAR(20),
    ano INT,
    trimestre VARCHAR(10),
    valor_despesas DECIMAL(15, 2), -- DECIMAL é melhor para valores monetários que FLOAT
    FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans)
);

-- Tabela de Despesas Agregadas (Para consulta rápida/Cache)
CREATE TABLE IF NOT EXISTS despesas_agregadas (
    razao_social VARCHAR(255),
    uf CHAR(2),
    total_despesas DECIMAL(15, 2),
    media_trimestral DECIMAL(15, 2),
    desvio_padrao DECIMAL(15, 2),
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_despesas_ano_trimestre ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_operadoras_uf ON operadoras(uf);
