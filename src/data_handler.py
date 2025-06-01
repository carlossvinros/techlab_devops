import pandas as pd
import os
from typing import Dict, List, Optional, Any
import traceback 

def carregar_planilhas_entrada(diretorio_input: str, nomes_arquivos_esperados: List[str]) -> Optional[Dict[str, pd.DataFrame]]:
    dataframes: Dict[str, pd.DataFrame] = {}
    print("--- Iniciando Etapa 1: Carregamento das Planilhas de Entrada ---")
    if not os.path.isdir(diretorio_input):
        print(f"  [ERRO] O diretório de input especificado não existe: {diretorio_input}")
        return None
    for nome_arquivo in nomes_arquivos_esperados:
        caminho_completo = os.path.join(diretorio_input, nome_arquivo)
        if not os.path.isfile(caminho_completo):
            print(f"  [ERRO] Arquivo esperado não encontrado: {caminho_completo}")
            return None 
        try:
            chave_df = nome_arquivo.replace('.xlsx', '')
            dataframes[chave_df] = pd.read_excel(caminho_completo)
            print(f"  [OK] Planilha '{nome_arquivo}' carregada como DataFrame '{chave_df}'. "
                  f"({len(dataframes[chave_df])} linhas)")
        except Exception as e:
            print(f"  [ERRO] Ocorreu um erro inesperado ao ler o arquivo '{nome_arquivo}': {e}")
            return None
    if len(dataframes) == len(nomes_arquivos_esperados):
        print("Todas as planilhas de entrada foram carregadas com sucesso.")
        print("--- Etapa 1 Concluída ---")
        return dataframes
    else:
        print("  [ERRO] Nem todas as planilhas esperadas puderam ser carregadas.")
        print("--- Etapa 1 Falhou ---")
        return None

def consolidar_e_calcular_custos(
    dataframes_brutos: Dict[str, pd.DataFrame], 
    mapeamento_colunas: Dict[str, Any]
) -> Optional[pd.DataFrame]:
    func_prefix = "[consolidar_e_calcular_custos]"
    print(f"\n--- Iniciando Etapa 3: Consolidação e Cálculo de Custos ---")

    if not dataframes_brutos or not mapeamento_colunas:
        print(f"{func_prefix} ERRO: DataFrames brutos ou mapeamento de colunas não fornecidos.")
        return None

    dataframes_padronizados: Dict[str, pd.DataFrame] = {}
    nomes_custos_individuais_padronizados = [] 

    for nome_df_original, df_bruto in dataframes_brutos.items():
        if nome_df_original not in mapeamento_colunas:
            print(f"{func_prefix} ALERTA: Mapeamento não encontrado para '{nome_df_original}'. Pulando.")
            continue
        mapa_atual = mapeamento_colunas[nome_df_original]
        col_orig_nome = mapa_atual['coluna_original_nome']
        col_orig_cpf = mapa_atual['coluna_original_cpf']
        col_orig_custo = mapa_atual['coluna_original_custo_principal']
        nome_pad_custo = mapa_atual['nome_padronizado_custo']
        colunas_necessarias_originais = [col_orig_nome, col_orig_cpf, col_orig_custo]
        if not all(col in df_bruto.columns for col in colunas_necessarias_originais):
            print(f"{func_prefix} ERRO: Colunas mapeadas {colunas_necessarias_originais} não encontradas em '{nome_df_original}'. Disponíveis: {list(df_bruto.columns)}")
            return None
        try:
            df_temp = df_bruto[colunas_necessarias_originais].copy()
            df_temp.rename(columns={
                col_orig_nome: "Nome_Padronizado", 
                col_orig_cpf: "CPF_Padronizado",    
                col_orig_custo: nome_pad_custo      
            }, inplace=True)
            df_temp["CPF_Padronizado"] = df_temp["CPF_Padronizado"].astype(str).str.replace(r'\D', '', regex=True)
            if nome_df_original != "colaboradores":
                df_temp.drop_duplicates(subset=["CPF_Padronizado"], keep='first', inplace=True)
            dataframes_padronizados[nome_df_original] = df_temp
            nomes_custos_individuais_padronizados.append(nome_pad_custo) 
            print(f"{func_prefix} DataFrame '{nome_df_original}' padronizado. Colunas: {list(df_temp.columns)}")
        except KeyError as ke:
            print(f"{func_prefix} ERRO de Chave em '{nome_df_original}': {ke}. Verifique mapeamento."); return None
        except Exception as e:
            print(f"{func_prefix} ERRO ao padronizar '{nome_df_original}': {e}"); traceback.print_exc(); return None
            
    if "colaboradores" not in dataframes_padronizados:
        print(f"{func_prefix} ERRO: DataFrame 'colaboradores' padronizado é essencial."); return None

    df_consolidado = dataframes_padronizados["colaboradores"].copy()
    print(f"{func_prefix} Iniciando merge dos DataFrames...")
    for nome_df_original_loop, df_custo_atual in dataframes_padronizados.items():
        if nome_df_original_loop == "colaboradores": continue
        mapa_custo_atual = mapeamento_colunas[nome_df_original_loop]
        nome_coluna_custo_especifico = mapa_custo_atual['nome_padronizado_custo']
        if "CPF_Padronizado" in df_custo_atual.columns and nome_coluna_custo_especifico in df_custo_atual.columns:
            df_para_merge = df_custo_atual[["CPF_Padronizado", nome_coluna_custo_especifico]]
            df_consolidado = pd.merge(df_consolidado, df_para_merge, on="CPF_Padronizado", how="left")
            print(f"{func_prefix} Merge com '{nome_df_original_loop}' realizado.")
        else:
            print(f"{func_prefix} ALERTA: '{nome_df_original_loop}' sem 'CPF_Padronizado' ou '{nome_coluna_custo_especifico}'. Merge pulado.")

    for col_custo in nomes_custos_individuais_padronizados:
        if col_custo in df_consolidado.columns:
            df_consolidado[col_custo] = df_consolidado[col_custo].fillna(0)
        else:
            print(f"{func_prefix} ALERTA: Coluna de custo '{col_custo}' ausente após merges. Adicionando com valor 0.")
            df_consolidado[col_custo] = 0
            
    print(f"{func_prefix} Calculando subtotais de custos...")
    custo_unimed_col = mapeamento_colunas.get("unimed", {}).get("nome_padronizado_custo", "Custo_Unimed")
    custo_gympass_col = mapeamento_colunas.get("gympass", {}).get("nome_padronizado_custo", "Custo_Gympass")
    custo_github_col = mapeamento_colunas.get("github", {}).get("nome_padronizado_custo", "Custo_GitHub")
    custo_google_col = mapeamento_colunas.get("google_workspace", {}).get("nome_padronizado_custo", "Custo_GoogleWorkspace")

    df_consolidado["Centro_Custo_Beneficios"] = df_consolidado.get(custo_unimed_col, 0) + df_consolidado.get(custo_gympass_col, 0)
    print(f"{func_prefix} Coluna 'Centro_Custo_Beneficios' calculada.")
    
    df_consolidado["Centro_Custo_Ferramentas"] = df_consolidado.get(custo_github_col, 0) + df_consolidado.get(custo_google_col, 0)
    print(f"{func_prefix} Coluna 'Centro_Custo_Ferramentas' calculada.")

    print(f"{func_prefix} Calculando Custo Geral Total...")
    
    colunas_para_soma_total = [mapa_col['nome_padronizado_custo'] for mapa_col in mapeamento_colunas.values() if mapa_col['nome_padronizado_custo'] in df_consolidado.columns]

    if not colunas_para_soma_total:
        print(f"{func_prefix} ERRO: Nenhuma coluna de custo primário para somar em Custo_Geral_Total.")
        return None
        
    df_consolidado["Custo_Geral_Total"] = df_consolidado[colunas_para_soma_total].sum(axis=1)
    print(f"{func_prefix} Custo Geral Total calculado.")
    
    col_orig_depto = mapeamento_colunas.get("colaboradores", {}).get("coluna_original_departamento")
    if col_orig_depto and col_orig_depto in dataframes_brutos["colaboradores"].columns:
        df_consolidado["Departamento"] = dataframes_brutos["colaboradores"][col_orig_depto]
    elif "Departamento" in dataframes_brutos["colaboradores"].columns: 
        df_consolidado["Departamento"] = dataframes_brutos["colaboradores"]["Departamento"]
    if "Departamento" in df_consolidado.columns:
        print(f"{func_prefix} Coluna 'Departamento' adicionada/confirmada.")

    print(f"--- Etapa 3 Concluída: Consolidação e Cálculos Finalizados ---")
    return df_consolidado