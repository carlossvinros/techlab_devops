import pandas as pd
import os
from typing import Dict, Any 
import traceback 

def gerar_relatorio_excel(
    df_final_calculado: pd.DataFrame, 
    mapeamento_colunas: Dict[str, Any],
    caminho_output_dir: str, 
    nome_arquivo_output: str
) -> bool:
    func_prefix = "[gerar_relatorio_excel]"
    print(f"\n--- Iniciando Geração do Relatório Excel ---")

    if df_final_calculado is None or df_final_calculado.empty:
        print(f"{func_prefix} ERRO: DataFrame final está vazio ou não foi fornecido.")
        return False

    try:
        colunas_relatorio = ["CPF_Padronizado", "Nome_Padronizado"]
        if "Departamento" in df_final_calculado.columns:
            colunas_relatorio.append("Departamento")
        
        coluna_salario = mapeamento_colunas.get("colaboradores", {}).get("nome_padronizado_custo", "Salario_Base")
        if coluna_salario in df_final_calculado.columns:
            colunas_relatorio.append(coluna_salario)
        
        custos_individuais_ferramentas = []
        custos_individuais_beneficios = []

        if mapeamento_colunas.get("github", {}).get("nome_padronizado_custo") in df_final_calculado.columns:
            custos_individuais_ferramentas.append(mapeamento_colunas["github"]["nome_padronizado_custo"])
        if mapeamento_colunas.get("google_workspace", {}).get("nome_padronizado_custo") in df_final_calculado.columns:
            custos_individuais_ferramentas.append(mapeamento_colunas["google_workspace"]["nome_padronizado_custo"])
        
        if mapeamento_colunas.get("gympass", {}).get("nome_padronizado_custo") in df_final_calculado.columns:
            custos_individuais_beneficios.append(mapeamento_colunas["gympass"]["nome_padronizado_custo"])
        if mapeamento_colunas.get("unimed", {}).get("nome_padronizado_custo") in df_final_calculado.columns:
            custos_individuais_beneficios.append(mapeamento_colunas["unimed"]["nome_padronizado_custo"])

        colunas_relatorio.extend(sorted(custos_individuais_ferramentas))
        if "Centro_Custo_Ferramentas" in df_final_calculado.columns:
            colunas_relatorio.append("Centro_Custo_Ferramentas")

        colunas_relatorio.extend(sorted(custos_individuais_beneficios))
        if "Centro_Custo_Beneficios" in df_final_calculado.columns:
            colunas_relatorio.append("Centro_Custo_Beneficios")
        
        if "Custo_Geral_Total" in df_final_calculado.columns:
            colunas_relatorio.append("Custo_Geral_Total")
        
        colunas_existentes_no_df = [col for col in colunas_relatorio if col in df_final_calculado.columns]
        df_para_exportar = df_final_calculado[colunas_existentes_no_df]

        os.makedirs(caminho_output_dir, exist_ok=True)
        caminho_completo_output = os.path.join(caminho_output_dir, nome_arquivo_output)
        df_para_exportar.to_excel(caminho_completo_output, index=False)
        print(f"{func_prefix} Relatório salvo com sucesso em: {caminho_completo_output}")
        print(f"--- Geração do Relatório Excel Concluída ---")
        return True
    except Exception as e:
        print(f"{func_prefix} ERRO ao gerar o relatório Excel: {e}")
        traceback.print_exc()
        return False