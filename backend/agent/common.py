"""
Shared common code for both course outline generators.
"""
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Dict, List, Optional
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import AgentState
import uuid

load_dotenv()

# Setup tools using the new @tool decorator
serper = GoogleSerperAPIWrapper()

@tool
def web_search(query: str) -> str:
    """Useful for when you need more information from an online search."""
    return serper.run(query)

tools = [web_search]

# Setup LLM using init_chat_model
model = init_chat_model("openai:gpt-4o-mini")

# Setup memory/checkpointer for conversation persistence
memory = MemorySaver()

# Define custom state extending AgentState
class CustomAgentState(AgentState):
    topic: str
    number_of_classes: int
    file_contents: Optional[List[Dict[str, str]]]

# Define context for runtime data
@dataclass
class Context:
    thread_id: str

def build_system_prompt(topic: str, number_of_classes: int, file_contents: Optional[List[Dict[str, str]]]) -> str:
    """Build a comprehensive system prompt for the agent."""
    prompt_parts = [
        "You are a helpful educational assistant.",
        f"Please create a course outline on '{topic}' with {number_of_classes} classes.",
        "You can use the available tools to gather more information any time."
    ]
    
    # Add file contents to the prompt if available
    if file_contents and len(file_contents) > 0:
        prompt_parts.append("\n\n--- Reference Materials ---")
        for file_info in file_contents:
            filename = file_info.get("filename", "Unknown file")
            content = file_info.get("content", "")
            prompt_parts.append(f"\n\nFile: {filename}\n{content}")
        prompt_parts.append("\n\nUse the above reference materials to inform the course outline.")
    
    return "\n".join(prompt_parts)

def generate_thread_id(thread_id: str | None) -> str:
    """Generate or return existing thread ID."""
    return thread_id if thread_id else str(uuid.uuid4())
