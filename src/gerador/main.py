from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from .agent_creation.agent import agent_creation, tools
from dotenv import load_dotenv

load_dotenv(override=True)


def edge_condicional(state: MessagesState) -> str:
    if state["messages"][-1].tool_calls:
      return "tools"

    return END


def build_graph():
    tool_node = ToolNode(tools)

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_creation)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", edge_condicional, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def execute_graph(input: str) -> str:
    initial_state = MessagesState(messages=[HumanMessage(input)])
    graph = build_graph()

    result = graph.invoke(initial_state)
    return result["messages"]


if __name__ == "__main__":
    messages = execute_graph(input("$ "))
    for message in messages:
        print(message.content)
        if isinstance(message, AIMessage) and message.tool_calls:
            print(f"Tool Call: {message.tool_calls}")
        print()