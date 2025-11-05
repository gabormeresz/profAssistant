"""
Course outline generator using markdown streaming.
Streams content token-by-token in markdown format.
"""
from typing import Dict, List
from langchain.agents import create_agent
from typing import Dict, List, Optional
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import AgentState
from dotenv import load_dotenv
from dataclasses import dataclass
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
class CourseOutlineAgentState(AgentState):
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


async def run_markdown_course_outline_generator(
    message: str, 
    topic: str = "", 
    number_of_classes: int = 1, 
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None
):
    """
    Run the LangChain agent with markdown streaming output.
    Streams tokens as they are generated.
    
    Args:
        message: The main user message/prompt (optional additional context)
        topic: The topic/subject for the lesson plan
        number_of_classes: Number of classes in the lesson plan
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
        file_contents: Optional list of file contents with filename and content
    
    Returns:
        Generator that yields content chunks in markdown format
    """
    try:
        # Use existing thread ID or create a new one
        thread_id = generate_thread_id(thread_id)
        
        # Build the system prompt with all the context
        system_prompt = build_system_prompt(
            topic if topic else "general education",
            number_of_classes if number_of_classes > 0 else 1,
            file_contents
        )
        
        # Add markdown formatting instruction
        system_prompt += "\nFormat the response in markdown with class titles as headings and bullet points for key topics under each class."
        
        # Create a new agent instance with the dynamic system prompt and memory
        current_agent = create_agent(
            model=model,
            tools=tools,
            state_schema=CourseOutlineAgentState,
            context_schema=Context,
            system_prompt=system_prompt,
            checkpointer=memory
        )
        
        # Prepare messages - only add user message if provided
        messages = []
        if message and message.strip():
            messages.append({"role": "user", "content": message})
        
        # Prepare the initial state
        initial_state = {
            "messages": messages,
            "topic": topic if topic else "general education",
            "number_of_classes": number_of_classes if number_of_classes > 0 else 1,
            "file_contents": file_contents
        }
        
        # Create context
        context = Context(thread_id=thread_id)
        
        # Create config with thread_id for checkpointer
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # First, yield the thread_id as metadata (with a special marker)
        yield f"__THREAD_ID__:{thread_id}\n"
        
        # Stream events from the agent
        async for event in current_agent.astream_events(
            initial_state, 
            context=context,
            config=config,  # type: ignore
            version="v2"
        ):
            kind = event.get("event")
            
            # Stream LLM tokens as they are generated
            # Note: node name changed from "agent" to "model" in v1.0
            if kind == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        yield content
                    
    except Exception as e:
        yield f"Error while generating content: {str(e)}\n"
