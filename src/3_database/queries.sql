-- Query 1: Top 5 operadoras com maior crescimento percentual de despesas
-- (Comparando primeiro e último trimestre disponíveis no banco)
WITH Trimestres AS (
    SELECT MIN(CONCAT(ano, trimestre)) as inicio, MAX(CONCAT(ano, trimestre)) as fim
    FROM despesas_consolidadas
),
DespesasInicio AS (
    SELECT registro_ans, valor_despesas
    FROM despesas_consolidadas, Trimestres
    WHERE CONCAT(ano, trimestre) = Trimestres.inicio
),
DespesasFim AS (
    SELECT registro_ans, valor_despesas
    FROM despesas_consolidadas, Trimestres
    WHERE CONCAT(ano, trimestre) = Trimestres.fim
)
SELECT 
    o.razao_social,
    ((df.valor_despesas - di.valor_despesas) / di.valor_despesas) * 100 as crescimento_percentual
FROM DespesasFim df
JOIN DespesasInicio di ON df.registro_ans = di.registro_ans
JOIN operadoras o ON df.registro_ans = o.registro_ans
ORDER BY crescimento_percentual DESC
LIMIT 5;

-- Query 2: Distribuição de despesas por UF (Top 5 estados)
SELECT 
    o.uf,
    SUM(d.valor_despesas) as total_despesas,
    AVG(d.valor_despesas) as media_por_operadora
FROM despesas_consolidadas d
JOIN operadoras o ON d.registro_ans = o.registro_ans
GROUP BY o.uf
ORDER BY total_despesas DESC
LIMIT 5;

-- Query 3: Operadoras com despesas acima da média geral em pelo menos 2 dos 3 trimestres
WITH MediaGeralPorTrimestre AS (
    SELECT ano, trimestre, AVG(valor_despesas) as media_geral
    FROM despesas_consolidadas
    GROUP BY ano, trimestre
),
OperadorasAcima AS (
    SELECT 
        d.registro_ans,
        COUNT(*) as trimestres_acima
    FROM despesas_consolidadas d
    JOIN MediaGeralPorTrimestre m ON d.ano = m.ano AND d.trimestre = m.trimestre
    WHERE d.valor_despesas > m.media_geral
    GROUP BY d.registro_ans
)
SELECT o.razao_social
FROM OperadorasAcima oa
JOIN operadoras o ON oa.registro_ans = o.registro_ans
WHERE oa.trimestres_acima >= 2;
