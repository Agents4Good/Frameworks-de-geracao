from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from .tools import client

model = ChatOpenAI(model="gpt-4o")
async def get_tools():
    return await client.get_tools()
    

async def mcp_agent(state: MessagesState):
    model_with_tools = model.bind_tools(await get_tools())
    print(await get_tools())
    print("-=-"*30)
    messages = state["messages"]
    response = await model_with_tools.ainvoke(messages)
    return {"messages": [response]}

