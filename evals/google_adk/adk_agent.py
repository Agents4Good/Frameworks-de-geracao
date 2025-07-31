import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from .adk_tools import adk_tavily_tool, get_curriculum_vitae

load_dotenv(override=True)

APP_NAME = "job_searcher_agent"
USER_ID = "111123"
SESSION_ID = "session_111123"


model = LiteLlm(
        api_key=os.getenv("DEEPINFRA_API_KEY"),
        base_url=os.getenv("DEEPINFRA_BASE_URL"),
        model=os.getenv("DEEPINFRA_MODEL")
    )




job_searcher_agent = Agent(
    name="job_searcher_agent",
    model=model,
    description="Searches a job for the user based on your curriculum vitae and preferences. (using meta-llama/Llama-3.3-70B-Instruct)",
    instruction="You are a job searcher agent. Your task is to search for a job for the user based on their curriculum vitae and preferences."
                "You will receive a curriculum vitae and preferences from the user, and you will search for a job that matches their profile using tools for web searching."
                "You should analyze the curriculum vitae and preferences to understand the user's skills, experience, and job preferences to use in searching."
                "You should use the Tavily search tool to find job offers that match the user's profile."
                "You must return the five best job offers that match the user's profile, with the job title, company name, location, link and a reason why you chose this job offer."
                "You should return the results in a markdown format.",
    tools=[adk_tavily_tool, get_curriculum_vitae],
)

async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=job_searcher_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent response:", final_response)

if __name__ == "__main__":
    # api_key=os.getenv("DEEPINFRA_API_KEY"),
    # base_url=os.getenv("DEEPINFRA_BASE_URL"),
    # model=os.getenv("DEEPINFRA_MODEL")
    # print(api_key, base_url, model)
    asyncio.run(call_agent_async(input("Enter your query: ")))