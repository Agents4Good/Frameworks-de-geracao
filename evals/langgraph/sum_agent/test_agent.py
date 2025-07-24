from deepeval.test_case import LLMTestCase, LLMTestCaseParams, ToolCall
from deepeval.metrics import GEval, ToolCorrectnessMetric
from deepeval import assert_test
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, ToolMessage
from agent import sum_agent, tools
from dotenv import load_dotenv

load_dotenv(override=True)

def edge_condicional(state: MessagesState) -> str:
  if state["messages"][-1].tool_calls:
    return "tools"

  return END

def build_graph():
    tool_node = ToolNode(tools)

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", sum_agent)
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

def get_tool_calls_names(messages: list) -> list:
    tool_calls = []
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_calls.append(ToolCall(name=message.name))
    return tool_calls

def test_case_1():
    INPUT = "quanto é 5+5+2?"
    system_result = execute_graph(INPUT)
    system_tool_calls = get_tool_calls_names(system_result)
    
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the information in 'actual output' is correct based on the information in 'expected output'.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT,
                           LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5
    )
    tool_call_metric = ToolCorrectnessMetric()
    
    test_case = LLMTestCase(
        input=INPUT,
        expected_output="A soma de 5 + 5 + 2 é 12.",
        actual_output=system_result[-1].content,
        
        expected_tools=[ToolCall(name="add"), ToolCall(name="add")],
        tools_called=system_tool_calls,
        
        retrieval_context=[
          "O Agente apenas responde perguntas de somas do usuário"]
    )
    
    assert_test(test_case, [correctness_metric, tool_call_metric])
