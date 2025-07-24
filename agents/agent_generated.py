import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import openai


class ToolResult:
    success: bool
    data: Any = None
    error_message: str = None

class MCPTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResult: pass


class SumTool(MCPTool):
    @property
    def name(self): return "sum"

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            num1 = params.get("num1")
            num2 = params.get("num2")
            if num1 is None or num2 is None:
                return ToolResult(success=False, error_message="num1 e num2 são necessários")
            return ToolResult(success=True, data={"result": num1 + num2})
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))


class MCPServer:
    def __init__(self): self.tools = {}

    def register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool

    async def execute_tool(self, name: str, params: Dict[str, Any]) -> ToolResult:
        tool = self.tools.get(name)
        return await tool.execute(params) if tool else ToolResult(False, error_message="Tool not found")


class LLMAgent:
    def __init__(self, api_key: str, model="gpt-4"):
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        self.mcp = MCPServer()
        self.mcp.register_tool(SumTool())
        self.history = []

    def _build_system_prompt(self) -> str:
        return (
            "Eu sou um agente que soma dois números inteiros.\n"
            "Para usar a ferramenta de soma, responda com: \n"
            "TOOL_CALL: sum\nPARAMS: {\"num1\": valor1, \"num2\": valor2}\n"
        )

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.5
        )
        return response.choices[0].message.content

    def _extract_tool_call(self, text: str) -> Dict[str, Any]:
        lines = text.splitlines()
        if "TOOL_CALL:" in text:
            tool = lines[0].split(":")[1].strip()
            params = json.loads(lines[1].split(":", 1)[1].strip())
            return {"tool": tool, "params": params}
        return {}

    async def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": self._build_system_prompt()}] + self.history

        response = await self._call_llm(messages)
        tool_call = self._extract_tool_call(response)

        if tool_call:
            result = await self.mcp.execute_tool(tool_call["tool"], tool_call["params"])
            result_msg = json.dumps(result.data if result.success else {"erro": result.error_message})
            self.history.append({"role": "assistant", "content": result_msg})
            return result_msg

        self.history.append({"role": "assistant", "content": response})
        return response

async def main():
    agent = LLMAgent(api_key="sua-chave-openai-aqui")
    while True:
        prompt = input("Você: ")
        if prompt.lower() in ["sair", "exit"]: break
        resposta = await agent.chat(prompt)
        print("Agente:", resposta)

if __name__ == "__main__":
    asyncio.run(main())