import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import openai
from datetime import datetime
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPMessage:
    """Representa uma mensagem no protocolo MCP"""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta"""
    success: bool
    data: Any
    error_message: str = None

class MCPTool(ABC):
    """Classe abstrata para ferramentas MCP"""
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        pass


class WebSearchTool(MCPTool):
    """Ferramenta para pesquisa web"""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Realiza pesquisas na web"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termo de pesquisa"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            query = params.get("query")
            max_results = params.get("max_results", 5)
            
            # Simulação de pesquisa web (substitua por API real como SerpAPI)
            results = [
                {
                    "title": f"Resultado {i+1} para '{query}'",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"Este é um snippet de exemplo para {query}"
                }
                for i in range(max_results)
            ]
            
            return ToolResult(success=True, data={"results": results})
            
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))


class MCPServer:
    """Servidor MCP que gerencia ferramentas e comunicação"""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.message_history: List[MCPMessage] = []
    
    def register_tool(self, tool: MCPTool):
        """Registra uma nova ferramenta"""
        self.tools[tool.name] = tool
        logger.info(f"Ferramenta '{tool.name}' registrada")
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Executa uma ferramenta específica"""
        if tool_name not in self.tools:
            return ToolResult(success=False, error_message=f"Ferramenta '{tool_name}' não encontrada")
        
        tool = self.tools[tool_name]
        return await tool.execute(params)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Lista todas as ferramentas disponíveis"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def add_message(self, message: MCPMessage):
        """Adiciona mensagem ao histórico"""
        self.message_history.append(message)

class LLMAgent:
    """Agente IA que usa LLM e MCP"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.mcp_server = MCPServer()
        self.conversation_history = []
        
        # Registrar ferramentas
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Registra ferramentas padrão"""
        self.mcp_server.register_tool(WebSearchTool())
    
    async def process_message(self, user_input: str) -> str:
        """Processa mensagem do usuário"""
        try:
            # Adicionar mensagem do usuário ao histórico
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Preparar mensagem para o LLM com informações sobre ferramentas
            system_message = self._build_system_message()
            
            messages = [
                {"role": "system", "content": system_message},
                *self.conversation_history[-10:]  # Últimas 10 mensagens
            ]
            
            # Primeira chamada ao LLM
            response = await self._call_llm(messages)
            
            # Verificar se o LLM quer usar ferramentas
            tool_calls = self._extract_tool_calls(response)
            
            if tool_calls:
                # Executar ferramentas solicitadas
                tool_results = await self._execute_tool_calls(tool_calls)
                
                # Adicionar resultados ao contexto e fazer nova chamada
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user", 
                    "content": f"Resultados das ferramentas: {json.dumps(tool_results, indent=2)}"
                })
                
                final_response = await self._call_llm(messages)
            else:
                final_response = response
            
            # Adicionar resposta ao histórico
            self.conversation_history.append({
                "role": "assistant",
                "content": final_response
            })
            
            return final_response
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return f"Desculpe, ocorreu um erro: {str(e)}"
    
    def _build_system_message(self) -> str:
        """Constrói mensagem de sistema com informações sobre ferramentas"""
        tools_info = self.mcp_server.list_tools()
        
        system_msg = """Você é um assistente IA avançado que pode usar ferramentas via MCP (Model Context Protocol).

        Ferramentas disponíveis:
        """
        for tool in tools_info:
            system_msg += f"\n- {tool['name']}: {tool['description']}"
            system_msg += f"\n  Parâmetros: {json.dumps(tool['parameters'], indent=2)}"
        
        system_msg += """

        Para usar uma ferramenta, responda no formato:
        TOOL_CALL: nome_da_ferramenta
        PARAMS: {"param1": "valor1", "param2": "valor2"}

        Caso contrário, responda normalmente ao usuário.
        """
        return system_msg
    
    async def _call_llm(self, messages: List[Dict]) -> str:
        """Chama o LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro na chamada LLM: {e}")
            raise
    
    def _extract_tool_calls(self, response: str) -> List[Dict]:
        """Extrai chamadas de ferramentas da resposta do LLM"""
        tool_calls = []
        lines = response.split('\n')
        
        i = 0
        while i < len(lines):
            if lines[i].startswith("TOOL_CALL:"):
                tool_name = lines[i].replace("TOOL_CALL:", "").strip()
                if i + 1 < len(lines) and lines[i + 1].startswith("PARAMS:"):
                    try:
                        params_str = lines[i + 1].replace("PARAMS:", "").strip()
                        params = json.loads(params_str)
                        tool_calls.append({
                            "tool": tool_name,
                            "params": params
                        })
                    except json.JSONDecodeError:
                        logger.error(f"Erro ao parsear parâmetros: {params_str}")
                i += 2
            else:
                i += 1
        
        return tool_calls
    
    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Executa chamadas de ferramentas"""
        results = []
        
        for call in tool_calls:
            tool_name = call["tool"]
            params = call["params"]
            
            result = await self.mcp_server.execute_tool(tool_name, params)
            results.append({
                "tool": tool_name,
                "params": params,
                "result": result.data if result.success else None,
                "error": result.error_message if not result.success else None
            })
        
        return results

# Exemplo de uso
async def main():
    # Configure sua chave da API OpenAI
    API_KEY = "sua-chave-openai-aqui"
    if API_KEY == "sua-chave-openai-aqui":
        print("⚠️  Por favor, configure sua chave da API OpenAI")
        return
    
    # Criar agente
    agent = LLMAgent(API_KEY)
    
    print("=== Agente IA com LLM e MCP ===")
    print("Digite 'sair' para encerrar")
    print("Ferramentas disponíveis: filesystem, web_search, calculator")
    print()
    
    while True:
        try:
            user_input = input("Você: ").strip()
            
            if user_input.lower() in ['sair', 'quit', 'exit']:
                print("Agente: Até logo! 👋")
                break
            
            if not user_input:
                continue
            
            # Processar mensagem
            response = await agent.process_message(user_input)
            print(f"Agente: {response}\n")
            
        except KeyboardInterrupt:
            print("\nAgente: Até logo! 👋")
            break
        except Exception as e:
            print(f"Erro: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())