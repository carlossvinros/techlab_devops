# Projeto de Rateio de Custos com IA

## 🎯 Visão Geral do Projeto

Este projeto automatiza o processo de rateio de custos de uma empresa, consolidando dados de múltiplas planilhas (colaboradores, ferramentas de software, benefícios) para gerar um relatório final detalhado por colaborador. A principal característica inteligente do sistema é o uso de um Modelo de Linguagem Grande (LLM) para realizar o mapeamento semântico de colunas com nomes variados nas planilhas de entrada para um esquema padronizado.

O desenvolvimento foi guiado pela necessidade de criar uma solução flexível e adaptável, evitando scripts com lógica de tratamento de dados pré-definida e inflexível para a etapa de mapeamento.

## 🚀 Solução Proposta

O sistema é implementado em Python e segue um pipeline de três etapas principais:

1.  **Etapa 1: Leitura e Carregamento de Dados**
    * As planilhas de entrada no formato `.xlsx` (localizadas em `data/input/`) são lidas utilizando a biblioteca Pandas e carregadas em DataFrames.

2.  **Etapa 2: Mapeamento Inteligente de Colunas com LLM**
    * Para cada planilha carregada, os nomes de suas colunas são enviados a um Modelo de Linguagem Grande (LLM), especificamente o `llama3-8b-8192` acessado via API da Groq através do LiteLLM.
    * O LLM é instruído a identificar as colunas que correspondem a conceitos chave (Nome do Colaborador, CPF, Custo Principal da Planilha) com base em sua compreensão semântica, mesmo que os nomes das colunas variem entre as planilhas.
    * O LLM retorna os nomes das colunas originais identificadas, que são então processados para criar um dicionário de mapeamento padronizado. Este dicionário guia a transformação dos dados na etapa seguinte.

3.  **Etapa 3: Consolidação, Cálculo de Custos e Geração do Relatório**
    * Utilizando o mapeamento gerado na Etapa 2, os DataFrames são padronizados (colunas renomeadas, CPFs limpos).
    * Os DataFrames padronizados são unidos (merge) usando o CPF como chave principal.
    * São calculados os custos individuais por colaborador para cada ferramenta e benefício.
    * São calculados subtotais para "Centro de Custo Benefícios" e "Centro de Custo Ferramentas".
    * O "Custo Geral Total" por colaborador é calculado (incluindo salário e todos os outros custos).
    * Um relatório final consolidado é gerado como um arquivo `.xlsx` na pasta `data/output/`.


## 📂 Estrutura do Diretório
techlab_devops/
├── .gitignore          # Especifica arquivos ignorados pelo Git
├── README.md           
├── requirements.txt    # Dependências Python do projeto
├── main.py             # Script principal para executar o pipeline
│
├── data/
│   ├── input/          # Local para colocar as planilhas .xlsx de entrada
│   │   ├── colaboradores.xlsx
│   │   ├── github.xlsx
│   │   ├── gympass.xlsx
│   │   ├── google_workspace.xlsx
│   │   └── unimed.xlsx
│   └── output/         # Onde o relatório final .xlsx será gerado
│       └── (Relatorio_Rateio_Custos.xlsx)
│
└── src/
├── init.py
├── data_handler.py     # Funções para carregar dados e consolidar/calcular
├── agent_mapper.py     # Lógica para interagir com o LLM e obter o mapeamento 
└── report_generator.py # Função para gerar o arquivo Excel final 

## 🛠️ Tecnologias Utilizadas

* **Python 3.9+**
* **Pandas:** Para manipulação e análise de dados tabulares.
* **LiteLLM:** Para interação simplificada com diversas APIs de LLMs.
* **Groq API:** Para acesso ao modelo de linguagem `llama3-8b-8192` (ou outro configurado).
* **python-dotenv:** Para gerenciamento de variáveis de ambiente (como chaves de API).
* **Openpyxl:** Utilizado internamente pelo Pandas para ler e escrever arquivos Excel (`.xlsx`).

*Nota sobre Frameworks de Agentes:* Durante o desenvolvimento, foi explorado o uso do framework CrewAI. No entanto, devido a desafios técnicos na integração específica do LLM (Groq) com as abstrações de LLM do LangChain/CrewAI no ambiente de desenvolvimento, optou-se por uma interação direta com o LLM via LiteLLM para a tarefa de mapeamento, mantendo o espírito de uma solução "agente" onde o LLM realiza a tomada de decisão inteligente.

## ⚙️ Configuração e Instalação

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/carlossvinros/techlab_devops
    cd techlab_devops
    ```

2.  **Crie e Ative um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # No Linux/macOS
    # .venv\Scripts\activate    # No Windows
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione suas credenciais da API Groq e o nome do modelo:
      ```env
      GROQ_API_KEY="sua_chave_api_real_da_groq_aqui"
      GROQ_MODEL_NAME="llama3-8b-8192" # Exemplo
      ```
    * **Importante:** Substitua `"sua_chave_api_real_da_groq_aqui"` pela sua chave de API válida da Groq. O modelo `llama3-8b-8192` é um exemplo; use o modelo configurado no seu ambiente Groq.

## ▶️ Como Executar

1.  **Prepare os Arquivos de Entrada:**
    * Coloque as 5 planilhas Excel (`colaboradores.xlsx`, `github.xlsx`, `gympass.xlsx`, `google_workspace.xlsx`, `unimed.xlsx`) dentro da pasta `data/input/`.
    * Certifique-se de que os nomes dos arquivos e as colunas relevantes dentro deles correspondem semanticamente ao que o LLM foi instruído a procurar (conforme detalhado nos prompts em `src/agent_mapper.py`).

2.  **Execute o Script Principal:**
    A partir da raiz do projeto, execute:
    ```bash
    python main.py
    ```

3.  **Verifique a Saída:**
    * Acompanhe os logs no terminal para o progresso de cada etapa.
    * O relatório final, chamado `Relatorio_Rateio_Custos.xlsx` (ou o nome definido em `main.py`), será gerado na pasta `data/output/`.
    * Logs de execução detalhados de cada chamada ao LLM para mapeamento de planilhas (se o `output_log_file` estiver ativo no `Crew` dentro do `agent_mapper.py` - atualmente é dinâmico) podem ser encontrados como `crew_log_<nome_planilha>.json`.

## 📊 Formato dos Dados

* **Entrada:** 5 arquivos Excel (`.xlsx`). O sistema espera que as colunas contenham informações semanticamente relacionadas a nomes de colaboradores, CPFs e valores de custos/salários, mesmo que os cabeçalhos exatos das colunas variem.
* **Saída (`Relatorio_Rateio_Custos.xlsx`):**
    * `CPF_Padronizado`
    * `Nome_Padronizado`
    * `Departamento` 
    * `Salario_Base`
    * `Custo_GitHub`
    * `Custo_GoogleWorkspace`
    * `Centro_Custo_Ferramentas` (soma dos custos de GitHub e Google Workspace)
    * `Custo_Gympass`
    * `Custo_Unimed`
    * `Centro_Custo_Beneficios` (soma dos custos de Gympass e Unimed)
    * `Custo_Geral_Total` (soma do Salário Base e todos os custos individuais de ferramentas e benefícios)


## 🧠 O Papel do Agente de IA

Embora a implementação final para a interação com o LLM utilize chamadas diretas via LiteLLM em vez da estrutura formal de `Agent` do framework CrewAI (decisão tomada devido a desafios de integração específicos), o sistema ainda emprega um componente de IA de forma "agente". O LLM atua como o "cérebro" para a tarefa de mapeamento semântico, interpretando os nomes das colunas e tomando decisões sobre como padronizá-los. O código Python ao redor orquestra essas chamadas e aplica as decisões do LLM, cumprindo o requisito do desafio de usar IA para um tratamento de dados não-fixo e inteligente.