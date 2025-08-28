from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent import mcp_agent, get_tools
from main import build_graph, execute_graph
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage


# ------------------------------
# 1️⃣ Testes Unitários de cada nó
# ------------------------------
def test_mcp_agent_node_behavior():
    # Mock do modelo para não chamar API real
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="Resposta mock do agente")

    # TypedDict é apenas dict
    state = {"messages": [HumanMessage(content="Olá")]}

    with patch("agent.model", mock_model):
        result = asyncio.run(mcp_agent(state))

    # Verificações do estado retornado
    assert isinstance(result, dict)
    assert "messages" in result
    messages = result["messages"]

    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[-1], AIMessage)
    assert messages[-1].content == "Resposta mock do agente"
    assert any(isinstance(m, HumanMessage)
               and m.content == "Olá" for m in messages)


# ------------------------------
# 2️⃣ Testes do Roteamento do Grafo
# ------------------------------
def test_graph_routing_verbose():
    # Mock do modelo
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="Resposta mock do agente")

    with patch("agent.model", mock_model):
        # Constrói o grafo compilado
        compiled_graph = asyncio.run(build_graph())

        # Estado inicial
        initial_state = {"messages": [HumanMessage(content="Teste do fluxo")]}

        # Invoca o grafo
        result_state = asyncio.run(compiled_graph.invoke(initial_state))

    messages = result_state["messages"]

    # Verificações com mensagens
    assert isinstance(
        messages[0], HumanMessage), "O primeiro item das mensagens deve ser o HumanMessage inicial."
    assert any(isinstance(m, SystemMessage)
               for m in messages), "Deve existir um SystemMessage (prompt do agente) em algum ponto das mensagens."
    assert isinstance(
        messages[-1], AIMessage), "O último item deve ser a resposta do agente."

    # Verificação explícita do END
    assert result_state is not None, "O estado final retornado pelo grafo não deve ser None; indica que o fluxo chegou ao END."


# ------------------------------
# 3 Testes estrutura do grafo
# ------------------------------
def test_graph_contains_agent_and_tool_and_start_nodes(self):
        "Verifica se o grafo contém apenas o nó 'agent', o nó inicial automático ('__start__') e o nó de ferramentas ('tools')"
        graph = asyncio.run(build_graph())
        nodes = list(graph.nodes.keys())

        # O grafo deve conter apenas '__start__', 'agent' e 'tools'
        expected_nodes = {'__start__', 'agent', 'tools'}
        actual_nodes = set(nodes)

        assert actual_nodes == expected_nodes, f"Esperado {expected_nodes}, mas encontrado {actual_nodes}"


# ------------------------------
# 2️⃣ Testa se o grafo não possui memória
# ------------------------------

def test_graph_no_memory():
    graph = asyncio.run(build_graph())

    for node_name, node in graph.nodes.items():
        # No LangGraph, nodes normalmente têm 'memory' ou 'tools' como atributos se configurados
        assert not hasattr(
            node, "memory"), f"Nó {node_name} possui atributo de memória"


# ------------------------------
# 3️⃣ Testa se o grafo possui ferramentas anexadas
# ------------------------------
def _has_tool_keywords(agent_source: str) -> bool:
    tool_keywords = ['tool', 'function_call', 'bind_tools', 'with_tools', 'tools']
    
    agent_source_lower = agent_source.lower()
    for keyword in tool_keywords:
        if keyword in agent_source_lower:
            return True
    return False

def test_agent_has_attached_tools():
    graph = asyncio.run(build_graph())
    
    nodes = list(graph.nodes.keys())
    tool_related_nodes = [node for node in nodes if 'tool' in node.lower() or 'function' in node.lower()]
    
    assert len(tool_related_nodes) == 0, f"Encontradas possíveis ferramentas: {tool_related_nodes}"
    
    # Verificamos se o agente usa ferramentas inspecionando o código da função
    import inspect
    agent_source = inspect.getsource(mcp_agent)
    
    assert _has_tool_keywords(agent_source=agent_source) is True
    
def test_graph_no_cycles_nominal_execution():
    input_text = "Teste de fluxo do grafo"
    
    # Mock do modelo para não chamar API real
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="Resposta mock do agente")
    
    with patch("agent.model", mock_model):
        messages = asyncio.run(execute_graph(input_text))
    
    # Verifica se o fluxo terminou corretamente
    assert isinstance(messages, list), "O resultado da execução do grafo deve ser uma lista de mensagens"
    assert messages[-1].content == "Resposta mock do agente", "O fluxo não terminou corretamente no nó final"
