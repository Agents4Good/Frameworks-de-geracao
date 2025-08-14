import os
from langchain_mcp_adapters.client import MultiServerMCPClient


client = MultiServerMCPClient(
    {
        "github": {
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
            },
            "transport": "streamable_http",
        }
    }
)