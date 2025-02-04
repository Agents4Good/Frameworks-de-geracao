from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from typing_extensions import Dict, TypedDict, Literal, Dict, Annotated

# The key to connect with the LLM
MODEL_API_KEY = "API_KEY"

# Instantiating the LLM that will be used
    # First Example: OpenAI
model = ChatOpenAI(model="gpt-4-turbo", api_key=MODEL_API_KEY)

# Creating the State that will be used in the Graph
# If the State only needs the messages of humans, system or AI, use the 'MessagesState' class
class CustomState(MessagesState):
    """
        Documentation explaining for what proporse the attribute will be used.
    """
    attribute1: Annotated[dict, "description of the attribute1"] = {
        "dict_key": str,
        "dict_value": []
    }
    """
        Documentation explaining for what proporse the attribute will be used.
    """
    attribute2: Annotated[list[str], "description of the attribute2"]
    
    
def agent1(state: CustomState) -> CustomState:
    system_prompt = """
    System Prompt that will be given to the LLM
    """
    # Updating the list of messages with the prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Sending the messages to the LLM
    response = model.invoke(messages)
    
    # Updating the State as needed
    state["attribute1"] = response.content

    # Updating the list of messages with the response, without the previous System Prompt
    state["messages"].append(response)
    
    # Return the updated list of messages
    return state


def agent2(state: CustomState) -> CustomState:
    system_prompt = """
    System Prompt that will be given to the LLM
    """
    # Updating the list of messages with the prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Sending the messages to the LLM
    response = model.invoke(messages)
    
    # Updating the State as needed
    state["attribute1"] = response.content

    # Updating the list of messages with the response, without the previous System Prompt
    state["messages"].append(response)
    
    # Return the updated list of messages
    return state


# Function to inicialize the graph 
def creating_graph():
    # Creating the Graph
        # First Example: StateGraph
    builder = StateGraph(CustomState)
    
    # Adding nodes (Agents and Tools)
    builder.add_node("agent1", agent1)
    builder.add_node("agent2", agent2)
    
    # Adding the edges of the graph (transictions)
    builder.add_edge(START, "agent1")
    builder.add_edge("agent1", "agent2")
    builder.add_edge("agent2", END)
    
    graph = builder.compile()
    return graph

def main():
    # Human prompt to the multiagent system
    human_message = "Human Prompt"
    
    # Creating the initial state
    initial_state = CustomState(messages=[HumanMessage(content=human_message)], 
                                attribute1='', attribute2='')
    
    graph = creating_graph()
    
    # Creating a view of the result for the user
    for event in graph.stream(initial_state):
        print("\n--- Event Step ---")
        for value in event.values():
            if isinstance(value, dict) and 'messages' in value:
                for message in value['messages']:
                    if isinstance(message, HumanMessage):
                        prefix = "Usuário"
                    elif isinstance(message, AIMessage):
                        prefix = "LLM"
                    elif isinstance(message, SystemMessage):
                        prefix = "Sistema"
                    else:
                        prefix = "Outro"

                    print(f"{prefix}: {message.content}")