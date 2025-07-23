import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

def test_case():
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5,
        model="gpt-3.5-turbo"
    )
    test_case = LLMTestCase(
        input="What if these shoes don't fit?",
        # Replace this with the actual output from your LLM application
        actual_output="""
        import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import openai


@dataclass
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
        print("chamou ferramenta")
        try:
            numbers = params.get("numbers", [])
            return ToolResult(success=True, data={"result": sum(numbers)})
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
            "Você é um agente que soma números inteiros.\n"
            "Para executar a soma, responda com:\n"
            "TOOL_CALL: sum\nPARAMS: {\"numbers\": [num1, num2, num3, ...]}\n"
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
    agent = LLMAgent(api_key="")  # Substitua pela sua chave real")
    while True:
        prompt = input("Você: ")
        if prompt.lower() in ["sair", "exit"]: break
        resposta = await agent.chat(prompt)
        print("Agente:", resposta)

if __name__ == "__main__":
    asyncio.run(main())
        """,
        expected_output="""
        import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import openai


@dataclass
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


class HelloTool(MCPTool):
    @property
    def name(self): return "say_hello"

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "Mundo")
        return ToolResult(success=True, data={"greeting": f"Olá, {name}!"})


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
        self.mcp.register_tool(HelloTool())
        self.history = []

    def _build_system_prompt(self) -> str:
        return (
            "Você pode usar ferramentas via MCP.\n"
            "Para isso, responda com:\n"
            "TOOL_CALL: <nome>\nPARAMS: {...}\n"
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
        """,
        retrieval_context=["All customers are eligible for a 30 day full refund at no extra costs."]
    )
    assert_test(test_case, [correctness_metric])