from langchain.tools import tool
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper

load_dotenv()

# Setup tools using the new @tool decorator
serper = GoogleSerperAPIWrapper()

@tool
def web_search(query: str) -> str:
    """Useful for when you need more information from an online search."""
    return serper.run(query)
