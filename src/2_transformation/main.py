import pandas as pd
import requests
import zipfile
import os
import logging
from io import BytesIO
from pathlib import Path

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_RAW = BASE_DIR / "data" / "raw"
INPUT_CSV = DATA_PROCESSED / "consolidado_despesas.csv"
OUTPUT_CSV = DATA_PROCESSED / "despesas_agregadas.csv"
OUTPUT_ZIP = BASE_DIR / "Teste_Gustavo.zip" # Nome genérico, o usuário renomeia

CADASTRO_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

def download_cadastro():
    """Baixa o arquivo de operadoras ativas"""
    logging.info("Baixando cadastro de operadoras...")
    target_path = DATA_RAW / "cadastro_operadoras.csv"
    
    try:
        r = requests.get(CADASTRO_URL, verify=False)
        if r.status_code != 200:
             logging.error(f"Erro ao baixar cadastro: {r.status_code}")
             return None
        
        with open(target_path, 'wb') as f:
            f.write(r.content)
        return target_path
    except Exception as e:
        logging.error(f"Erro ao baixar cadastro: {e}")
        return None

def main():
    if not os.path.exists(INPUT_CSV):
        logging.error(f"Arquivo de entrada {INPUT_CSV} não encontrado. Execute a Etapa 1 primeiro.")
        return

    # 1. Carregar Consolidado
    logging.info("Carregando dados consolidados...")
    df_despesas = pd.read_csv(INPUT_CSV, sep=';', encoding='utf-8', dtype={'CNPJ': str})
    
    # 2. Validações
    # Valores Positivos
    df_despesas = df_despesas[df_despesas['ValorDespesas'] > 0]
    
    # 3. Carregar e Enriquecer com Cadastro
    cad_path = download_cadastro()
    if cad_path:
        logging.info("Carregando cadastro...")
        try:
            # O cadastro usa ponto e vírgula e latin1
            df_cad = pd.read_csv(cad_path, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
            
            # Limpar aspas se houver
            df_cad.columns = df_cad.columns.str.replace('"', '').str.strip()
            
            # Join: No consolidado, 'CNPJ' contém o Registro ANS (conforme etapa 1)
            # No cadastro, o Registro ANS está em 'REGISTRO_OPERADORA'
            df_merged = pd.merge(
                df_despesas, 
                df_cad, 
                left_on='CNPJ', 
                right_on='REGISTRO_OPERADORA', 
                how='left'
            )
            
            # Prioriza Razao_Social do cadastro
            if 'Razao_Social' in df_merged.columns:
                df_merged['RazaoSocial'] = df_merged['Razao_Social'].fillna(df_merged['RazaoSocial'])
            
            # Adicionar UF e Modalidade se existirem
            cols_to_keep = ['RazaoSocial', 'UF', 'ValorDespesas', 'Trimestre', 'Ano', 'CNPJ_y', 'Modalidade']
            # CNPJ_y é o CNPJ real vindo do cadastro
            
            # Limpeza final
            df_final = df_merged.copy()
            if 'CNPJ_y' in df_final.columns:
                df_final['CNPJ_Real'] = df_final['CNPJ_y']
            
            df_agregado = df_final
        except Exception as e:
            logging.error(f"Erro ao processar cadastro: {e}. Usando dados brutos.")
            df_agregado = df_despesas.copy()
            df_agregado['UF'] = 'NI'
    else:
        df_agregado = df_despesas.copy()
        df_agregado['UF'] = 'NI'

    # 4. Agregação e Estatísticas
    logging.info("Calculando agregações...")
    
    # Garante que temos as colunas necessárias
    if 'UF' not in df_agregado.columns: df_agregado['UF'] = 'NI'
    if 'RazaoSocial' not in df_agregado.columns: df_agregado['RazaoSocial'] = df_agregado['CNPJ']

    # Agrupar por Operadora e UF
    stats = df_agregado.groupby(['RazaoSocial', 'UF'])['ValorDespesas'].agg(
        TotalDespesas='sum',
        MediaTrimestral='mean',
        DesvioPadrao='std'
    ).reset_index()
    
    # Preencher NaNs no Desvio Padrão (ocorre se houver apenas 1 registro)
    stats['DesvioPadrao'] = stats['DesvioPadrao'].fillna(0)
    
    # Ordenar por valor total
    stats.sort_values(by='TotalDespesas', ascending=False, inplace=True)
    
    # 5. Salvar
    stats.to_csv(OUTPUT_CSV, index=False, sep=';', encoding='utf-8')
    logging.info(f"Arquivo agregado salvo em {OUTPUT_CSV}")
    
    # Zipar final
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(OUTPUT_CSV, arcname="despesas_agregadas.csv")
    logging.info(f"ZIP Final criado: {OUTPUT_ZIP}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
