import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm 
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from .prompts import AGENT_CREATOR_PROMPT

load_dotenv(override=True)

model = LiteLlm(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL")
)

agent_creator = Agent(
    name="agent_creator",
    model=model,
    description="Agente responsável por criar agentes com base num template do google ADK e nas especificações do usuário.",
     
    instruction=AGENT_CREATOR_PROMPT,
)
