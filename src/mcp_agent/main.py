from dotenv import load_dotenv
load_dotenv(override=True)

from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage
from .github_agent.agent import mcp_agent, get_tools
import asyncio


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
        print("-=-"*30)
    return "Execução concluída"



github_response = asyncio.run(execute_graph("Quais são os meus repositórios?"))
print(github_response)