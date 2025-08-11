from dotenv import load_dotenv
from pathlib import Path
from typing import TypedDict


load_dotenv(override=True)

current_file_path = Path(__file__).resolve().parent

GENERATED_PATH = current_file_path.parent / "arquivos_gerados"
GENERATED_PATH.mkdir(parents=True, exist_ok=True)

AGENT_DIR = GENERATED_PATH / "agent"
AGENT_DIR.mkdir(parents=True, exist_ok=True)

AGENT_PATH = AGENT_DIR / "agent.py"
TOOLS_PATH = AGENT_DIR / "tools.py"
DOCUMENTATION_PATH = AGENT_DIR / "documentation.md"
MAIN_PATH = GENERATED_PATH / "main.py"

AGENT_CACHE = {
    "name": "",
    "prompt": ""
}

AGENT_TEMPLATE = '''
import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from tools import {tools}

load_dotenv(override=True)

model = LiteLlm(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL")
)

root_agent = Agent(
    name="{agent_name}",
    model=model,
    description="{description}",

    instruction="{prompt}",
    tools=[{tools}],
)

'''
def criar_agente(agent_name: str, description: str, prompt: str, tools_name: list) -> str:
    """
    Cria e salva um agente em um arquivo .py

    :param agent_name: Nome do agente que será criado
    :param description: Descrição do agente que será criado
    :param prompt: Prompt do agente que será gerado
    :param tools_name: Lista de nomes das tools que serão usadas pelo agente gerado

    :return: String com o nome do agente e as tools que ele utiliza
    """
    tools_list = ", ".join(tools_name)
    
    agent = AGENT_TEMPLATE.format(
        agent_name=agent_name,
        description=description,
        prompt=prompt,
        tools=tools_list
    )

    AGENT_CACHE["name"] = agent_name
    AGENT_CACHE["prompt"] = prompt

    with open(AGENT_PATH, 'w', encoding='utf-8') as file:
        file.write(agent)

    return f"O agente {agent_name} foi criado com as seguintes ferramentas {tools_list}"

TOOL_TEMPLATE = '''
def {tool_name}({params}):
    """
    {description}
  
    {params_doc}
  
    :return: {return_doc}
    """
    {code}
'''

class ParamSpec(TypedDict):
    name: str
    type_: str
    description: str


def criar_tool(tool_name: str, params: list[ParamSpec ], description: str, code: str, return_doc: str) -> str:
    """
    Gera uma tool no formato do Google ADK com base nas informações fornecidas.

    :param tool_name: Nome da função/tool.
    :param params: Lista de Objetos ParamSpec no formato: 
    :param description: Descrição geral da função/tool.
    :param code: Código da função/tool em Python.
    :param return_doc: Documentação do retorno da função/tool.

    :return: String com a definição da função/tool.
    """

    params_str = ", ".join([f"{p['name']}: {p['type_']}" for p in params])
    params_doc = "\n    ".join([f":param {p['name']}: {p['desc']}" for p in params])

    tool_code = TOOL_TEMPLATE.format(
        tool_name=tool_name,
        params=params_str,
        description=description,
        params_doc=params_doc,
        return_doc=return_doc,
        code=code
    )

    TOOLS_PATH.touch(exist_ok=True)

    with open(TOOLS_PATH, "r+", encoding="utf-8") as f:
        existing_content = f.read()
        f.seek(0, 2)

        if existing_content.strip():
            f.write("\n\n" + tool_code)
        else:
            f.write(tool_code)

    return f"A tool '{tool_name}' foi adicionada ao arquivo tools.py com sucesso."

DOCUMENTATION_TEMPLATE = """
# {agent_name}

Tipo: Agente ADK 
Role: {role}

### Exemplos de uso

```
{exemple}
```

### System Prompt
```
{prompt}
```

### Modo de Ativação

O agente deve ser ativado quando:
{activation_mode}

### Modelo de linguagem

É necessário que o modelo seja capaz de utilizar ferramentas.

Modelo utilizado em testes:
- openai/gpt-4

### Tools

{tools_descriprion}

### Testes e validação

Foi utilizado para a realização de testes a biblioteca Deepeval do Python
"""

def criar_documentacao(role: str, example: str, activation_mode: str, tools_description: list[str]) -> str:
    """
    Gera uma documentação estruturada para um agente.

    :param role: Descrição do papel/persona do agente.
    :param exemple: Exemplo de uso do agente.
    :param activation_mode: Descrição das condições ou modo de ativação do agente (ex. entrada do usuário).
    :param tools_description: Lista contendo descrições das ferramentas usadas pelo agente.

    :return: Confirmação que a documentação foi criada.
    """
    agent_name = AGENT_CACHE["name"]
    agent_prompt = AGENT_CACHE["prompt"]

    documentation_code = DOCUMENTATION_TEMPLATE.format(
        agent_name=agent_name,
        role=role,
        example=example,
        prompt=agent_prompt,
        activation_mode=activation_mode,
        tools_description=tools_description
    )

    with open(DOCUMENTATION_PATH, "w", encoding="utf-8") as f:
        f.write(documentation_code)

    return f"A documentação do agente {agent_name} foi criada com sucesso."