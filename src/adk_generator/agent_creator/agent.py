import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm 
from .prompts import AGENT_CREATOR_PROMPT
from .tools.tools import (
    criar_agente,
    criar_documentacao,
    criar_tool
    )

load_dotenv(override=True)

model = LiteLlm(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL")
)

root_agent = Agent(
    name="agent_creator",
    model=model,
    description="Agente responsável por criar agentes com base num template do google ADK e nas especificações do usuário.",
     
    instruction=AGENT_CREATOR_PROMPT,
    tools=[criar_agente, criar_tool, criar_documentacao]
)
