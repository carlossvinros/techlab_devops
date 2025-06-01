import litellm
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

def test_groq_call():
    print("--- Iniciando teste direto do LiteLLM com Groq ---")
    
    api_key = os.getenv("GROQ_API_KEY")
    model_name_from_env = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant") # Fornece um padrão
    
    if not api_key:
        print("ERRO: GROQ_API_KEY não encontrada nas variáveis de ambiente. Verifique seu arquivo .env.")
        return

    litellm_model_name = f"groq/{model_name_from_env}"
    
    print(f"Modelo a ser usado: {litellm_model_name}")
    print(f"API Key (primeiros/últimos 5 chars): {api_key[:5]}...{api_key[-5:]}" if api_key else "Nenhuma API Key")

    messages = [
        {"role": "user", "content": "Translate 'hello world' to French."}
    ]

    try:
        print("Tentando chamar litellm.completion...")
        litellm.set_verbose = True


        response = litellm.completion(
            model=litellm_model_name,
            messages=messages,
            api_key=api_key, 
            temperature=0.1,
            max_tokens=50,
            timeout=30 
        )
        
        print("\nChamada bem-sucedida!")
        print("Resposta do LiteLLM:")
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            content = response.choices[0].message.content
            print(f"Conteúdo da mensagem: {content}")
        else:
            print("Resposta recebida, mas o conteúdo da mensagem está vazio ou malformado.")
            print("Detalhes da resposta:", response)


    except litellm.exceptions.AuthenticationError as e:
        print(f"\nERRO DE AUTENTICAÇÃO com LiteLLM/Groq: {e}")
        print("Verifique se sua GROQ_API_KEY é válida e tem permissões.")
        traceback.print_exc()
    except litellm.exceptions.APIConnectionError as e:
        print(f"\nERRO DE CONEXÃO com LiteLLM/Groq: {e}")
        print("Verifique sua conexão com a internet e se os endpoints da Groq estão acessíveis.")
        traceback.print_exc()
    except litellm.exceptions.RateLimitError as e:
        print(f"\nERRO DE LIMITE DE TAXA com LiteLLM/Groq: {e}")
        traceback.print_exc()
    except litellm.exceptions.NotFoundError as e: 
        print(f"\nERRO - MODELO NÃO ENCONTRADO com LiteLLM/Groq: {e}")
        print(f"Verifique se o nome do modelo '{litellm_model_name}' está correto e disponível na sua conta Groq.")
        traceback.print_exc()
    except Exception as e:
        print(f"\nUM ERRO INESPERADO OCORREU durante a chamada LiteLLM/Groq: {e}")
        print("Detalhes do erro:")
        traceback.print_exc() 

if __name__ == "__main__":
    test_groq_call()