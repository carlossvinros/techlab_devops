import os
import json
import time
import traceback
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
import litellm

load_dotenv()

def configurar_llm_direct() -> Optional[Dict[str, str]]:
    """Carrega configuração do LLM (modelo e API key) do ambiente."""
    print("[configurar_llm_direct] Carregando configuração do LLM...")
    api_key = os.getenv("GROQ_API_KEY")
    model_name_from_env = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192") 

    if not api_key:
        print("[configurar_llm_direct] ERRO CRÍTICO: GROQ_API_KEY não encontrada. Verifique o .env.")
        return None
    
    litellm_model_name = f"groq/{model_name_from_env}"

    print(f"[configurar_llm_direct] Configuração LLM: Modelo='{litellm_model_name}', API Key Carregada (parcial): {api_key[:5]}...")
    return {"model": litellm_model_name, "api_key": api_key}

def processar_mapeamento_identificado(
    nome_planilha: str, 
    col_original_nome: str, 
    col_original_cpf: str, 
    col_original_custo_principal: str
) -> Dict[str, Any]:
    """
    Processa as colunas identificadas pelo LLM para uma planilha e retorna o dicionário de mapeamento padronizado.
    Esta função atua como a lógica da nossa "ferramenta".
    """
    func_prefix = "[processar_mapeamento_identificado]"
    print(f"{func_prefix} Recebido para '{nome_planilha}': Nome='{col_original_nome}', CPF='{col_original_cpf}', Custo='{col_original_custo_principal}'")

    mapping_parcial_dict = {
        "coluna_original_nome": col_original_nome,
        "coluna_original_cpf": col_original_cpf,
        "coluna_original_custo_principal": col_original_custo_principal,
        "nome_padronizado_para_nome": "Nome_Colaborador", 
        "nome_padronizado_para_cpf": "CPF_Padronizado",    
    }
    cost_map = {
        "colaboradores": "Salario_Base", "github": "Custo_GitHub", "gympass": "Custo_Gympass",
        "google_workspace": "Custo_GoogleWorkspace", "unimed": "Custo_Unimed"
    }
    if nome_planilha not in cost_map:
        print(f"{func_prefix} ERRO: Nome de planilha desconhecido '{nome_planilha}'.")
        return {"erro": f"Nome de planilha desconhecido '{nome_planilha}'."}
        
    mapping_parcial_dict["nome_padronizado_custo"] = cost_map[nome_planilha]
    
    result_dict = {nome_planilha: mapping_parcial_dict}
    print(f"{func_prefix} Mapeamento para '{nome_planilha}' processado: {json.dumps(result_dict)}")
    return result_dict

def obter_mapeamento_para_planilha_unica(
    llm_config: Dict[str, str], 
    nome_planilha_atual: str, 
    colunas_da_planilha_atual: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Envia um prompt ao LLM para mapear uma única planilha e espera um JSON com os nomes das colunas.
    """
    func_prefix = "[obter_mapeamento_para_planilha_unica]"
    
    system_prompt = """Você é um assistente especialista em análise de dados. Sua tarefa é identificar colunas específicas em um esquema de planilha fornecido."""
    
    user_prompt = f"""
    Analise o esquema da planilha chamada '{nome_planilha_atual}' que tem as seguintes colunas: {colunas_da_planilha_atual}.

    Você DEVE identificar exatamente três colunas desta lista:
    1.  A coluna que representa o NOME COMPLETO do colaborador.
    2.  A coluna que representa o CPF (documento de identificação fiscal) do colaborador.
    3.  A coluna principal de CUSTO MONETÁRIO a ser extraída desta planilha específica.
        Lembre-se das dicas de coluna de custo:
        - Para 'colaboradores', a coluna de custo é 'Salario'.
        - Para 'github', a coluna de custo é 'Valor Mensal'.
        - Para 'gympass', a coluna de custo é 'Valor Mensal'.
        - Para 'google_workspace', a coluna de custo é 'Valor Mensal'.
        - Para 'unimed', a coluna de custo é 'Total'.

    Responda APENAS com um objeto JSON contendo as seguintes chaves com os nomes das colunas originais que você identificou:
    - "col_nome_identificada"
    - "col_cpf_identificada"
    - "col_custo_identificada"

    Exemplo de formato de resposta JSON esperado (APENAS O JSON):
    {{
      "col_nome_identificada": "Nome Original da Coluna Nome",
      "col_cpf_identificada": "Nome Original da Coluna CPF",
      "col_custo_identificada": "Nome Original da Coluna Custo"
    }}

    Use sua melhor capacidade semântica para encontrar as colunas corretas, mesmo que os nomes tenham pequenas variações (ex: 'Assinante' para nome, 'Documento' para CPF).
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    print(f"{func_prefix} Enviando prompt para LLM para planilha '{nome_planilha_atual}'...")
    
    try:
        response = litellm.completion(
            model=llm_config["model"],
            messages=messages,
            api_key=llm_config["api_key"],
            temperature=0.0,
            max_tokens=300, 
            timeout=30
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            llm_response_content = response.choices[0].message.content.strip()
            print(f"{func_prefix} Resposta bruta do LLM para '{nome_planilha_atual}': '{llm_response_content}'")
            
            try:
                if llm_response_content.startswith("```json"):
                    llm_response_content = llm_response_content[len("```json"):].strip()
                if llm_response_content.endswith("```"):
                    llm_response_content = llm_response_content[:-len("```")].strip()

                identificacao_cols = json.loads(llm_response_content)
                
                chaves_necessarias = ["col_nome_identificada", "col_cpf_identificada", "col_custo_identificada"]
                if all(key in identificacao_cols for key in chaves_necessarias):
                    return processar_mapeamento_identificado(
                        nome_planilha=nome_planilha_atual,
                        col_original_nome=identificacao_cols["col_nome_identificada"],
                        col_original_cpf=identificacao_cols["col_cpf_identificada"],
                        col_original_custo_principal=identificacao_cols["col_custo_identificada"]
                    )
                else:
                    print(f"{func_prefix} ERRO: JSON do LLM não contém todas as chaves esperadas para '{nome_planilha_atual}'. Recebido: {identificacao_cols}")
                    return None
            except json.JSONDecodeError as e:
                print(f"{func_prefix} ERRO: Falha ao decodificar JSON da resposta do LLM para '{nome_planilha_atual}': {e}")
                print(f"String que causou o erro: '{llm_response_content}'")
                return None
        else:
            print(f"{func_prefix} ERRO: Resposta do LLM malformada ou vazia para '{nome_planilha_atual}'. Detalhes: {response}")
            return None
            
    except litellm.exceptions.RateLimitError as rle:
        print(f"{func_prefix} ERRO DE RATE LIMIT da API Groq para '{nome_planilha_atual}': {rle}")
        raise 
    except Exception as e:
        print(f"{func_prefix} ERRO CRÍTICO em litellm.completion para '{nome_planilha_atual}': {type(e).__name__} - {e}")
        print(traceback.format_exc())
        raise

def obter_mapeamento_colunas(esquemas_originais: Dict[str, List[str]]) -> Optional[Dict]:
    """
    Orquestra o mapeamento de colunas iterando sobre cada planilha e chamando o LLM.
    """
    print("\n--- Iniciando Etapa 2: Mapeamento de Colunas (Loop Direto com LiteLLM) ---")
    
    llm_config = configurar_llm_direct()
    if not llm_config:
        print("  [ERRO CRÍTICO] Configuração do LLM falhou. Mapeamento não pode prosseguir.")
        print("--- Etapa 2 Falhou ---")
        return None

    mapeamento_final_agregado: Dict[str, Any] = {}
    nomes_planilhas_processadas = list(esquemas_originais.keys())
    
    ATRASO_ENTRE_CHAMADAS_SEGUNDOS = 10 

    for i, (nome_planilha, colunas_planilha) in enumerate(esquemas_originais.items()):
        print(f"\n[obter_mapeamento_colunas] Processando planilha {i+1}/{len(esquemas_originais)}: '{nome_planilha}'...")
        
        if i > 0: 
            print(f"Aguardando {ATRASO_ENTRE_CHAMADAS_SEGUNDOS} segundos para evitar rate limit...")
            time.sleep(ATRASO_ENTRE_CHAMADAS_SEGUNDOS)
        
        try:
            mapeamento_parcial = obter_mapeamento_para_planilha_unica(
                llm_config, 
                nome_planilha, 
                colunas_planilha
            )
            
            if mapeamento_parcial:
                if "erro" in mapeamento_parcial: 
                    print(f"  Erro ao processar mapeamento para '{nome_planilha}': {mapeamento_parcial['erro']}")
                else:
                    mapeamento_final_agregado.update(mapeamento_parcial)
                    print(f"Mapeamento para '{nome_planilha}' agregado com sucesso.")
            else:
                print(f"  Não foi possível obter mapeamento para '{nome_planilha}'.")

        except litellm.exceptions.RateLimitError:
             print(f"  [RATE LIMIT] Atingido para '{nome_planilha}'. Interrompendo o processo de mapeamento.")
             break 
        except Exception as e:
            print(f"  [ERRO INESPERADO] ao processar '{nome_planilha}': {type(e).__name__} - {e}")
            print(f"  Continuando para a próxima planilha, se houver.")
            
    if len(mapeamento_final_agregado) == len(nomes_planilhas_processadas):
        print("\n--- Etapa 2 Concluída com Sucesso (Mapeamento Direto com LiteLLM) ---")
    else:
        print(f"\n--- Etapa 2 Concluída com Mapeamento Parcial ({len(mapeamento_final_agregado)}/{len(nomes_planilhas_processadas)} planilhas) ---")
    
    if mapeamento_final_agregado:
        print("\nMapeamento Final Agregado:")
        print(json.dumps(mapeamento_final_agregado, indent=2, ensure_ascii=False))
        return mapeamento_final_agregado
    elif not nomes_planilhas_processadas: 
        print("Nenhuma planilha fornecida para mapeamento.")
        return {}
    else: 
        print("Nenhuma planilha foi mapeada com sucesso.")
        return None


if __name__ == '__main__':
    print("Executando teste direto de agent_mapper.py (Loop Direto com LiteLLM)...")
    esquemas_teste = {
        'colaboradores': ['Nome', 'CPF', 'Departamento', 'Salario'],
        'github': ['Assinante', 'Documento', 'Data Ativacao', 'Copilot', 'Licença', 'Valor Mensal'],
        'gympass': ['Assinante', 'Documento', 'Plano', 'Valor Mensal'],
        'google_workspace': ['Assinante', 'Documento', 'Data Ativacao', 'Licença', 'Valor Mensal'],
        'unimed': ['Assinante', 'Documento', 'Plano', 'Total']
    }
        
    llm_config_teste = configurar_llm_direct()
    if not llm_config_teste:
        print("Teste direto não pode prosseguir: Configuração do LLM falhou.")
    else:
        print("\nIniciando teste da função obter_mapeamento_colunas com esquemas de teste...")
        mapeamento = obter_mapeamento_colunas(esquemas_teste)
        if mapeamento and len(mapeamento) > 0 :
            print("\nResultado do teste de mapeamento (Loop Direto com LiteLLM): OK")
        else:
            print("\nTeste de mapeamento (Loop Direto com LiteLLM) falhou ou não retornou mapeamentos.")