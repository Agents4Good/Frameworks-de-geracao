from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from tools import add
from dotenv import load_dotenv

load_dotenv(override=True)

model = ChatOpenAI(model="gpt-4o")

tools = [add]
model_with_tools = model.bind_tools(tools)

def sum_agent(state: MessagesState) -> MessagesState:
  prompt = SystemMessage(content="""
  Você é um assistente muito útil que responde as perguntas de matemática do usuário.
  Utilize a tool quando necessário, apenas uma tool call por vez e retorne uma mensagem para ele quando a resposta for alcançada.
  Responda em Português - BR.
  """)

  messages = state["messages"] + [prompt]

  return state["messages"].append(model_with_tools.invoke(messages))
