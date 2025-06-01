import os
import json
from dotenv import load_dotenv

load_dotenv() 

from src.data_handler import carregar_planilhas_entrada, consolidar_e_calcular_custos
from src.agent_mapper import obter_mapeamento_colunas 
from src.report_generator import gerar_relatorio_excel 

def run_pipeline():
    print("Iniciando Pipeline de Rateio de Custos (Completo)...")

    project_root_dir = os.path.dirname(os.path.abspath(__file__))
    input_data_dir = os.path.join(project_root_dir, 'data', 'input')
    output_data_dir = os.path.join(project_root_dir, 'data', 'output') 
    nome_arquivo_relatorio = "Relatorio_Rateio_Custos.xlsx"
    
    nomes_planilhas = [
        "colaboradores.xlsx", "github.xlsx", "gympass.xlsx",
        "google_workspace.xlsx", "unimed.xlsx"
    ]
    dataframes_brutos = carregar_planilhas_entrada(input_data_dir, nomes_planilhas)
    if dataframes_brutos is None:
        print("Pipeline interrompido: erro no carregamento dos dados (Etapa 1).")
        return

    esquemas_originais = {
        nome_df: list(df.columns) for nome_df, df in dataframes_brutos.items()
    }
    print("\nChamando LLM para obter o mapeamento de colunas...")
    mapeamento_colunas = obter_mapeamento_colunas(esquemas_originais)

    if mapeamento_colunas is None or not mapeamento_colunas : 
        print("Pipeline interrompido: erro ou nenhum mapeamento de colunas (Etapa 2).")
        return
    
    print("\nMapeamento de Colunas Final Recebido em main.py:")
    print(json.dumps(mapeamento_colunas, indent=2, ensure_ascii=False))

    df_final_calculado = consolidar_e_calcular_custos(dataframes_brutos, mapeamento_colunas)

    if df_final_calculado is None or df_final_calculado.empty:
        print("Pipeline interrompido: erro na consolidação ou cálculo de custos (Etapa 3).")
        return
    
    print("\nDataFrame Final Calculado (primeiras linhas):")
    print(df_final_calculado.head())

    sucesso_relatorio = gerar_relatorio_excel(
        df_final_calculado, 
        mapeamento_colunas, 
        output_data_dir, 
        nome_arquivo_relatorio
    )

    if sucesso_relatorio:
        print("\nPipeline de Rateio de Custos concluído com SUCESSO!")
    else:
        print("\nPipeline de Rateio de Custos concluído com ERROS na geração do relatório.")

if __name__ == "__main__":
    run_pipeline()