import asyncio
import json
import logging
import subprocess
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
from datetime import datetime
import aiohttp
import websockets

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPMessage:
    """Representa uma mensagem no protocolo MCP"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class ExternalMCPClient:
    """Cliente para conectar com MCP servers externos"""
    
    def __init__(self, server_command: List[str], server_args: Dict[str, str] = None):
        self.server_command = server_command
        self.server_args = server_args or {}
        self.process = None
        self.tools = []
        self.resources = []
        self.prompts = []
        self.message_id = 0
    
    def get_next_id(self) -> str:
        """Gera próximo ID de mensagem"""
        self.message_id += 1
        return str(self.message_id)
    
    async def start_server(self):
        """Inicia o MCP server externo"""
        try:
            # Configurar variáveis de ambiente para o server
            env = os.environ.copy()
            env.update(self.server_args)
            
            # Iniciar processo do server
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            logger.info(f"MCP Server iniciado: {' '.join(self.server_command)}")
            
            # Inicializar conexão
            await self._initialize_connection()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar MCP server: {e}")
            raise
    
    async def stop_server(self):
        """Para o MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP Server parado")
    
    async def _send_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Envia mensagem para o MCP server"""
        if not self.process:
            raise RuntimeError("MCP Server não está rodando")
        
        # Converter para JSON
        message_json = json.dumps(message.__dict__, default=str) + '\n'
        
        # Enviar mensagem
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()
        
        # Ler resposta
        response_line = await self.process.stdout.readline()
        response_data = json.loads(response_line.decode())
        
        return response_data
    
    async def _initialize_connection(self):
        """Inicializa conexão com o MCP server"""
        # Mensagem de inicialização
        init_message = MCPMessage(
            id=self.get_next_id(),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "Python MCP Client",
                    "version": "1.0.0"
                }
            }
        )
        
        response = await self._send_message(init_message)
        logger.info("Conexão MCP inicializada")
        
        # Listar ferramentas disponíveis
        await self._list_tools()
        await self._list_resources()
        await self._list_prompts()
    
    async def _list_tools(self):
        """Lista ferramentas disponíveis no server"""
        message = MCPMessage(
            id=self.get_next_id(),
            method="tools/list",
            params={}
        )
        
        response = await self._send_message(message)
        if 'result' in response and 'tools' in response['result']:
            self.tools = response['result']['tools']
            logger.info(f"Ferramentas disponíveis: {[tool['name'] for tool in self.tools]}")
    
    async def _list_resources(self):
        """Lista recursos disponíveis no server"""
        try:
            message = MCPMessage(
                id=self.get_next_id(),
                method="resources/list",
                params={}
            )
            
            response = await self._send_message(message)
            if 'result' in response and 'resources' in response['result']:
                self.resources = response['result']['resources']
                logger.info(f"Recursos disponíveis: {[res['uri'] for res in self.resources]}")
        except Exception as e:
            logger.debug(f"Server não suporta recursos: {e}")
    
    async def _list_prompts(self):
        """Lista prompts disponíveis no server"""
        try:
            message = MCPMessage(
                id=self.get_next_id(),
                method="prompts/list",
                params={}
            )
            
            response = await self._send_message(message)
            if 'result' in response and 'prompts' in response['result']:
                self.prompts = response['result']['prompts']
                logger.info(f"Prompts disponíveis: {[prompt['name'] for prompt in self.prompts]}")
        except Exception as e:
            logger.debug(f"Server não suporta prompts: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Chama uma ferramenta no MCP server"""
        message = MCPMessage(
            id=self.get_next_id(),
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        response = await self._send_message(message)
        return response
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Retorna informações sobre as ferramentas disponíveis"""
        return self.tools

class LLMAgentWithExternalMCP:
    """Agente IA que usa LLM e MCP servers externos"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.mcp_clients: Dict[str, ExternalMCPClient] = {}
        self.conversation_history = []
    
    async def add_mcp_server(self, name: str, server_command: List[str], server_args: Dict[str, str] = None):
        """Adiciona um MCP server externo"""
        client = ExternalMCPClient(server_command, server_args)
        await client.start_server()
        self.mcp_clients[name] = client
        logger.info(f"MCP server '{name}' adicionado")
    
    async def remove_mcp_server(self, name: str):
        """Remove um MCP server"""
        if name in self.mcp_clients:
            await self.mcp_clients[name].stop_server()
            del self.mcp_clients[name]
            logger.info(f"MCP server '{name}' removido")
    
    async def shutdown(self):
        """Para todos os MCP servers"""
        for name, client in self.mcp_clients.items():
            await client.stop_server()
        self.mcp_clients.clear()
    
    def _get_all_tools(self) -> List[Dict[str, Any]]:
        """Retorna todas as ferramentas de todos os MCP servers"""
        all_tools = []
        for server_name, client in self.mcp_clients.items():
            tools = client.get_tools_info()
            for tool in tools:
                tool['_server'] = server_name  # Adiciona info do server
                all_tools.append(tool)
        return all_tools
    
    def _build_system_message(self) -> str:
        """Constrói mensagem de sistema com informações sobre ferramentas"""
        all_tools = self._get_all_tools()
        
        if not all_tools:
            return "Você é um assistente IA. Responda às perguntas do usuário da melhor forma possível."
        
        system_msg = """Você é um assistente IA avançado que pode usar ferramentas via MCP (Model Context Protocol).

Ferramentas disponíveis:
"""
        for tool in all_tools:
            server_name = tool.get('_server', 'unknown')
            system_msg += f"\n- {tool['name']} (server: {server_name}): {tool.get('description', 'Sem descrição')}"
            if 'inputSchema' in tool:
                system_msg += f"\n  Schema: {json.dumps(tool['inputSchema'], indent=2)}"
        
        system_msg += """

Para usar uma ferramenta, responda no formato:
TOOL_CALL: nome_da_ferramenta
SERVER: nome_do_server
PARAMS: {"param1": "valor1", "param2": "valor2"}

Caso contrário, responda normalmente ao usuário.
"""
        return system_msg
    
    async def process_message(self, user_input: str) -> str:
        """Processa mensagem do usuário"""
        try:
            # Adicionar mensagem do usuário ao histórico
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Preparar mensagem para o LLM
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
                    "content": f"Resultados das ferramentas: {json.dumps(tool_results, indent=2, ensure_ascii=False)}"
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
    
    async def _call_llm(self, messages: List[Dict]) -> str:
        """Chama o LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
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
                server_name = None
                params = {}
                
                # Procurar SERVER e PARAMS nas próximas linhas
                j = i + 1
                while j < len(lines) and j < i + 4:  # Máximo 4 linhas à frente
                    if lines[j].startswith("SERVER:"):
                        server_name = lines[j].replace("SERVER:", "").strip()
                    elif lines[j].startswith("PARAMS:"):
                        try:
                            params_str = lines[j].replace("PARAMS:", "").strip()
                            params = json.loads(params_str)
                        except json.JSONDecodeError:
                            logger.error(f"Erro ao parsear parâmetros: {params_str}")
                    j += 1
                
                if server_name:
                    tool_calls.append({
                        "tool": tool_name,
                        "server": server_name,
                        "params": params
                    })
                
                i = j
            else:
                i += 1
        
        return tool_calls
    
    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Executa chamadas de ferramentas"""
        results = []
        
        for call in tool_calls:
            tool_name = call["tool"]
            server_name = call["server"]
            params = call["params"]
            
            if server_name not in self.mcp_clients:
                results.append({
                    "tool": tool_name,
                    "server": server_name,
                    "error": f"Server '{server_name}' não encontrado"
                })
                continue
            
            try:
                client = self.mcp_clients[server_name]
                response = await client.call_tool(tool_name, params)
                
                results.append({
                    "tool": tool_name,
                    "server": server_name,
                    "params": params,
                    "result": response.get('result'),
                    "error": response.get('error')
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "server": server_name,
                    "params": params,
                    "error": str(e)
                })
        
        return results

# Exemplo de configuração e uso
async def main():
    # Configure sua chave da API OpenAI
    OPENAI_API_KEY = "sua-chave-openai-aqui"  # Substitua pela sua chave real
    
    if OPENAI_API_KEY == "sua-chave-openai-aqui":
        print("⚠️  Por favor, configure sua chave da API OpenAI")
        return
    
    # Criar agente
    agent = LLMAgentWithExternalMCP(OPENAI_API_KEY)
    
    try:
        # Configurar MCP server do Slack
        # Você precisa configurar as variáveis de ambiente do Slack
        slack_env = {
            "SLACK_BOT_TOKEN": "xoxb-seu-token-aqui",  # Token do seu bot Slack
            "SLACK_APP_TOKEN": "xapp-seu-token-aqui"   # Token da sua app Slack
        }
        
        # Adicionar MCP server do Slack
        await agent.add_mcp_server(
            name="slack",
            server_command=["npx", "-y", "@modelcontextprotocol/server-slack"],
            server_args=slack_env
        )
        
        # Exemplo de outros MCP servers que você pode adicionar:
        
        # # Sistema de arquivos
        # await agent.add_mcp_server(
        #     name="filesystem",
        #     server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/caminho/para/diretorio"]
        # )
        
        # # GitHub
        # await agent.add_mcp_server(
        #     name="github",
        #     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
        #     server_args={"GITHUB_PERSONAL_ACCESS_TOKEN": "seu-token-github"}
        # )
        
        print("=== Agente IA com MCP Servers Externos ===")
        print("Digite 'sair' para encerrar")
        print("Digite 'ferramentas' para listar ferramentas disponíveis")
        print()
        
        while True:
            try:
                user_input = input("Você: ").strip()
                
                if user_input.lower() in ['sair', 'quit', 'exit']:
                    print("Agente: Até logo! 👋")
                    break
                
                if user_input.lower() == 'ferramentas':
                    tools = agent._get_all_tools()
                    if tools:
                        print("Ferramentas disponíveis:")
                        for tool in tools:
                            print(f"- {tool['name']} ({tool.get('_server', 'unknown')}): {tool.get('description', 'Sem descrição')}")
                    else:
                        print("Nenhuma ferramenta disponível")
                    print()
                    continue
                
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
    
    finally:
        # Limpar recursos
        await agent.shutdown()

# Instruções de instalação e configuração
def print_setup_instructions():
    instructions = """
=== INSTRUÇÕES DE CONFIGURAÇÃO ===

1. Instale as dependências:
   pip install openai aiohttp websockets

2. Instale Node.js (necessário para os MCP servers):
   https://nodejs.org/

3. Configure as variáveis de ambiente para o Slack:
   - Crie uma app Slack em https://api.slack.com/apps
   - Obtenha o Bot Token (xoxb-...) e App Token (xapp-...)
   - Configure as permissões necessárias

4. Configure sua chave da OpenAI:
   - Obtenha em https://platform.openai.com/api-keys

5. Execute o código!

Exemplos de uso com Slack:
- "Liste os canais do Slack"
- "Envie uma mensagem para o canal #general"
- "Busque mensagens recentes no canal #dev"
    """
    print(instructions)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_setup_instructions()
    else:
        asyncio.run(main())