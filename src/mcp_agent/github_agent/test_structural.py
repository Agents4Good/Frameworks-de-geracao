from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent import mcp_agent, get_tools
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

async def build_graph():
    tool_node = ToolNode(await get_tools())

    builder = StateGraph(MessagesState)
    builder.add_node("agent", mcp_agent)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
    )
    builder.add_edge("tools", "agent")

    return builder.compile()

async def execute_graph(input: str) -> str:
    initial_state = MessagesState(messages=[HumanMessage(input)])
    graph = await build_graph()

    async for update in graph.astream(initial_state, stream_mode="updates"):
        _, state = next(iter(update.items()))

        if not state or "messages" not in state:
            continue

        last_msg = state["messages"][-1]

        if getattr(last_msg, "tool_calls", None):
            print("Tool calls:", last_msg.tool_calls)
        else:
            print("Nova mensagem:", last_msg.content)
    return "Execução concluída"

# ------------------------------
# 1️⃣ Testes Unitários de cada nó
# ------------------------------
async def test_mcp_agent_node_behavior():
    # Mock do modelo para não chamar API real
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="Resposta mock do agente")

    # TypedDict é apenas dict
    state = {"messages": [HumanMessage(content="Olá")]}

    with patch("agent.model", mock_model):
        result = await mcp_agent(state)

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
async def test_graph_routing_verbose():
    # Mock do modelo
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="Resposta mock do agente")

    with patch("agent.model", mock_model):
        # Constrói o grafo compilado
        compiled_graph = await build_graph()

        # Estado inicial
        initial_state = {"messages": [HumanMessage(content="Teste do fluxo")]}

        # Invoca o grafo
        result_state = await compiled_graph.invoke(initial_state)

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
async def test_graph_contains_agent_and_tool_and_start_nodes(self):
        "Verifica se o grafo contém apenas o nó 'agent', o nó inicial automático ('__start__') e o nó de ferramentas ('tools')"
        graph = await build_graph()
        nodes = list(graph.nodes.keys())

        # O grafo deve conter apenas '__start__', 'agent' e 'tools'
        expected_nodes = {'__start__', 'agent', 'tools'}
        actual_nodes = set(nodes)

        assert actual_nodes == expected_nodes, f"Esperado {expected_nodes}, mas encontrado {actual_nodes}"


# ------------------------------
# 2️⃣ Testa se o grafo não possui memória
# ------------------------------

async def test_graph_no_memory():
    graph = await build_graph()

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

async def test_agent_has_attached_tools():
    graph = await build_graph()
    
    nodes = list(graph.nodes.keys())
    tool_related_nodes = [node for node in nodes if 'tool' in node.lower() or 'function' in node.lower()]
    
    assert len(tool_related_nodes) == 0, f"Encontradas possíveis ferramentas: {tool_related_nodes}"
    
    # Verificamos se o agente usa ferramentas inspecionando o código da função
    import inspect
    agent_source = inspect.getsource(mcp_agent)
    
    assert _has_tool_keywords(agent_source=agent_source) is True
    
async def test_graph_no_cycles_nominal_execution():
    input_text = "Teste de fluxo do grafo"
    
    # Mock do modelo para não chamar API real
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="Resposta mock do agente")
    
    with patch("agent.model", mock_model):
        messages = await execute_graph(input_text)
    
    # Verifica se o fluxo terminou corretamente
    assert isinstance(messages, list), "O resultado da execução do grafo deve ser uma lista de mensagens"
    assert messages[-1].content == "Resposta mock do agente", "O fluxo não terminou corretamente no nó final"
