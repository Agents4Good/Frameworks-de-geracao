from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from tools import client

model = ChatOpenAI(model="gpt-4o")

async def get_tools():
    tools = await client.get_tools()        
    filtered_tools = [
        t for t in tools
        if ("required" not in t.args_schema.keys()) or ("repo" in t.args_schema.get("required", []) or ("repositor" in t.name))
    ]
    return filtered_tools

async def mcp_agent(state: MessagesState):
    model_with_tools = model.bind_tools(await get_tools())
    messages = [SystemMessage("Você é um assistente que utiliza ferramentas do GitHub")] + state["messages"]
    print("*-"*30)
    print(messages[-1])
    print("*-"*30)
    response = await model_with_tools.ainvoke(messages)
    print(response)
    messages.append(response)
    
    return {"messages": messages}

