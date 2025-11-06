"""
Course outline generator using markdown streaming.
Streams content token-by-token in markdown format.
"""
from typing import Dict, List
from typing import Dict, List, Optional
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import AgentState
from langchain.agents import create_agent
from .tools import web_search
from .model import model
from dataclasses import dataclass
import uuid
from utils.context_builders import build_file_contents_message

# Setup tools list
tools = [web_search]

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

def build_system_prompt() -> str:
    """Build a simple system prompt for the agent."""
    system_prompt = """
    You are a helpful educational assistant that creates course outlines in markdown format. 
    Always stick to the topic and number of classes the user provided unless the user explicitly asks otherwise. 
    If the user provides reference materials (file uploads), use them as a reference only and do not copy them verbatim.
    Stick to the topic and number of classes even if the reference materials suggest otherwise,
    however try to extract the essence of the reference materials.
    Use headings for class titles and bullet points for key topics.
    You can use the available tools to gather more information any time.
    Only respond in markdown format and only the Course Outline as specified, no other text.
    """
    return system_prompt

def build_initial_user_message(topic: str, number_of_classes: int) -> str:
    """Build the initial user message with topic and number of classes."""
    return f"Please create a course outline on '{topic}' with {number_of_classes} classes. Format the response in markdown with class titles as headings and bullet points for key topics under each class."

def build_user_message(is_first_call: bool, topic: str, number_of_classes: int, message: str, file_contents: List[Dict[str, str]] | None) -> Dict[str, str]:
    """Build the user message dictionary."""
    # Prepare messages
    messages = ""
    
    # On first call (no existing thread_id), add the topic and number of classes
    if is_first_call:
        initial_message = build_initial_user_message(
            topic if topic else "general education",
            number_of_classes if number_of_classes > 0 else 1
        )
        messages += f"{initial_message}\n"
    
    # Add user message if provided
    if message and message.strip():
        messages += f"{message}\n\n"

    # Add file contents if provided
    if file_contents and len(file_contents) > 0:
        messages += f"{build_file_contents_message(file_contents)}\n"

    return {"role": "user", "content": messages}

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
        # Determine if this is the first call
        is_first_call = thread_id is None or not thread_id
        # Use existing thread ID or create a new one
        thread_id = generate_thread_id(thread_id)
        
        # Build the simple system prompt
        system_prompt = build_system_prompt()
        
        # Create a new agent instance with the dynamic system prompt and memory
        current_agent = create_agent(
            model=model,
            tools=tools,
            state_schema=CourseOutlineAgentState,
            context_schema=Context,
            system_prompt=system_prompt,
            checkpointer=memory
        )
        
        # Build user message
        user_message = build_user_message(
            is_first_call,
            topic,
            number_of_classes,
            message,
            file_contents)

        # Prepare the initial state
        initial_state = {
            "messages": user_message,
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
