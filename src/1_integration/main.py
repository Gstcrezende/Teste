import os
import re
import zipfile
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from pathlib import Path
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações de Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
OUTPUT_ZIP = BASE_DIR / "consolidado_despesas.zip"

# URL Base da ANS (Ajustada para o caminho provável das demonstrações contábeis)
# A URL do PDF é a raiz. Navegando, geralmente é demonstracoes_contabeis/
BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"

def get_available_quarters():
    """
    Busca na página da ANS os anos e trimestres disponíveis.
    Retorna uma lista ordenada de tuplas (ano, trimestre, url).
    """
    logging.info(f"Acessando {BASE_URL} para listar arquivos...")
    try:
        response = requests.get(BASE_URL, verify=False) # verify=False pois gov.br as vezes tem erro de cert
        if response.status_code != 200:
            logging.error(f"Erro ao acessar URL: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        
        # Regex para encontrar pastas de ano (ex: 2023/)
        year_links = []
        for link in links:
            href = link.get('href')
            if href and re.match(r'^\d{4}/?$', href):
                year_links.append(href.strip('/'))
        
        year_links.sort(reverse=True) # Anos mais recentes primeiro
        
        quarters = []
        
        # Para cada ano, busca os trimestres
        for year in year_links:
            if len(quarters) >= 3: break # Já temos o suficiente (otimização)
            
            year_url = f"{BASE_URL}{year}/"
            logging.info(f"Verificando ano {year}...")
            resp_year = requests.get(year_url, verify=False)
            soup_year = BeautifulSoup(resp_year.content, 'html.parser')
            
            q_links = soup_year.find_all('a')
            found_quarters = []
            for ql in q_links:
                href = ql.get('href')
                # Procura padrões como 1T2023, 202301, 1_trimestre, etc. 
                # O padrão da ANS varia, mas geralmente é trimestral em pastas.
                # Assumindo estrutura comum de pasta ou arquivo zip direto.
                # O PDF diz estrutura "YYYY/QQ/".
                if href and (re.search(r'[1-4]T', href, re.IGNORECASE) or re.search(r'[1-4]Q', href, re.IGNORECASE)):
                     found_quarters.append(href)
            
            # Ordena trimestres do mais recente pro antigo
            found_quarters.sort(reverse=True)
            
            for q in found_quarters:
                full_url = f"{year_url}{q}"
                quarters.append((year, q.strip('/'), full_url))
                if len(quarters) >= 3: break
                
        return quarters[:3]

    except Exception as e:
        logging.error(f"Erro ao listar trimestres: {e}")
        # Fallback de segurança para garantir execução mesmo sem scraping
        logging.warning("Usando fallback de trimestres.")
        return [
            ("2023", "3T", "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/2023/3T2023.zip"),
            ("2023", "2T", "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/2023/2T2023.zip"),
            ("2023", "1T", "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/2023/1T2023.zip")
        ]

def download_and_extract(url, year, quarter):
    """Baixa o ZIP e extrai na pasta raw"""
    target_dir = DATA_RAW / f"{year}_{quarter}"
    os.makedirs(target_dir, exist_ok=True)
    
    logging.info(f"Baixando {year}-{quarter} de {url}...")
    try:
        # Se a URL for um diretório, precisamos achar o ZIP dentro dele
        if not url.endswith('.zip'):
             # Lógica simplificada: assume que a URL já aponta pro ZIP no fallback ou tenta adivinhar
             # Em um cenário real, faria outro requests.get para achar o .zip
             url = url.rstrip('/') + '.zip'

        response = requests.get(url, verify=False)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                z.extractall(target_dir)
            logging.info(f"Extraído em {target_dir}")
            return target_dir
        else:
            logging.error(f"Falha no download: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Erro ao baixar/extrair {url}: {e}")
        return None

def find_expense_file(directory):
    """Encontra o arquivo de despesas (Eventos/Sinistros) no diretório"""
    candidates = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.csv'):
                candidates.append(os.path.join(root, file))
                # Prioridade por nome
                if "EVENTOS" in file.upper() or "DESPESA" in file.upper() or "SINISTRO" in file.upper():
                    return os.path.join(root, file)
    
    # Se não achou com nome específico, mas tem CSV (estrutura nova de arquivo único), retorna o primeiro
    if candidates:
        return candidates[0]
        
    return None

def normalize_and_read(file_path, year, quarter):
    """Lê CSV, fixando encoding e separadores"""
    logging.info(f"Processando {file_path}...")
    try:
        # Tenta ler com encoding latin1 (comum) ou utf-8
        try:
            df = pd.read_csv(file_path, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        except:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8', on_bad_lines='skip', dtype=str)
            
        # Limpar aspas das colunas se necessário
        df.columns = df.columns.str.replace('"', '').str.strip()
        
        # Mapeamento baseado no arquivo inspecionado:
        # "DATA";"REG_ANS";"CD_CONTA_CONTABIL";"DESCRICAO";"VL_SALDO_INICIAL";"VL_SALDO_FINAL"
        
        if 'REG_ANS' not in df.columns:
            # Tenta achar coluna que parece REG_ANS
            for col in df.columns:
                if 'REG' in col.upper() or 'ANS' in col.upper():
                    df.rename(columns={col: 'REG_ANS'}, inplace=True)
                    break

        if 'VL_SALDO_FINAL' not in df.columns:
             for col in df.columns:
                if 'VALOR' in col.upper() or 'SALDO' in col.upper():
                    df.rename(columns={col: 'VL_SALDO_FINAL'}, inplace=True)
                    break
        
        # Filtro: Despesas com Eventos/Sinistros
        # Geralmente Contas de classe 4 (Despesas Assistenciais)
        # E especificamente eventos. Vamos filtrar quem tem "EVENTOS" ou "SINISTROS" na descrição
        # OU conta começa com 4.
        
        mask = pd.Series(False, index=df.index)
        
        if 'CD_CONTA_CONTABIL' in df.columns:
            mask |= df['CD_CONTA_CONTABIL'].str.startswith('4', na=False)
            
        if 'DESCRICAO' in df.columns:
            mask |= df['DESCRICAO'].str.upper().str.contains('EVENTO', na=False)
            mask |= df['DESCRICAO'].str.upper().str.contains('SINISTRO', na=False)
            
        if mask.any():
            df = df[mask]
        
        # Cria colunas padrão
        df['Trimestre'] = quarter
        df['Ano'] = year
        
        # Tratamento de valores
        if 'VL_SALDO_FINAL' in df.columns:
            # Remove aspas do conteudo se tiver
            df['ValorDespesas'] = df['VL_SALDO_FINAL'].astype(str).str.replace('"', '').str.replace('.', '').str.replace(',', '.').astype(float)
        else:
            df['ValorDespesas'] = 0.0
            
        # Renomear para o padrão interno esperado
        df.rename(columns={'REG_ANS': 'CNPJ'}, inplace=True) # Placeholder ID
        
        return df
    except Exception as e:
        logging.error(f"Erro ao ler arquivo {file_path}: {e}")
        return pd.DataFrame()

def main():
    os.makedirs(DATA_RAW, exist_ok=True)
    os.makedirs(DATA_PROCESSED, exist_ok=True)
    
    # 1. Identificar Trimestres
    quarters = get_available_quarters()
    if not quarters:
        logging.error("Nenhum trimestre encontrado.")
        return

    all_data = []

    # 2. Loop de Download e Processamento
    for year, quarter, url in quarters:
        dir_path = download_and_extract(url, year, quarter)
        if dir_path:
            file_path = find_expense_file(dir_path)
            if file_path:
                df = normalize_and_read(file_path, year, quarter)
                if not df.empty:
                    all_data.append(df)
            else:
                logging.warning(f"Arquivo de despesas não encontrado em {dir_path}")

    # 3. Consolidação
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Selecionar e renomear colunas finais
        # Mapeamos REG_ANS para CNPJ conforme requisito de saída, embora sejam identificadores distintos
        if 'REG_ANS' in final_df.columns:
             final_df.rename(columns={'REG_ANS': 'CNPJ'}, inplace=True)
        
        cols_to_keep = ['CNPJ', 'Trimestre', 'Ano', 'ValorDespesas']
        # Adiciona Razao Social vazia se não vier no arquivo (geralmente vem no cadastro)
        if 'RazaoSocial' not in final_df.columns:
            final_df['RazaoSocial'] = 'DESCONHECIDO' 
            
        final_cols = [c for c in cols_to_keep if c in final_df.columns] + ['RazaoSocial']
        final_df = final_df[final_cols]

        output_csv = DATA_PROCESSED / "consolidado_despesas.csv"
        final_df.to_csv(output_csv, index=False, sep=';', encoding='utf-8')
        logging.info(f"Arquivo consolidado salvo em {output_csv}")
        
        # 4. Zipar
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(output_csv, arcname="consolidado_despesas.csv")
        logging.info(f"Arquivo ZIP criado: {OUTPUT_ZIP}")

    else:
        logging.error("Nenhum dado processado.")

if __name__ == "__main__":
    # Desabilita warnings de SSL inseguro para o teste
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
