from dotenv import load_dotenv
load_dotenv(override=True)

from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from agent import mcp_agent, get_tools
import asyncio


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
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

    result_state = await graph.ainvoke(initial_state)
    print(result_state)
    return result_state["messages"]


if __name__ == "__main__":
    asyncio.run(execute_graph(input("$ ")))