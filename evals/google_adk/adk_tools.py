import os
from dotenv import load_dotenv
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults

load_dotenv(override=True)

tavily_tool_instance = TavilySearchResults(
    max_results=10,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=False,
)

adk_tavily_tool = LangchainTool(tool=tavily_tool_instance)


def get_curriculum_vitae(path: str) -> str:
    """
    Reads the curriculum vitae from a file and returns its content.
    :param path: Path to the curriculum vitae file.
    :return: Content of the curriculum vitae.
    """
    if not path:
        raise ValueError("Path to the curriculum vitae file must be provided.")
    with open(path, 'r', encoding='utf-8') as file:
        curriculum_vitae = file.read()
    return curriculum_vitae