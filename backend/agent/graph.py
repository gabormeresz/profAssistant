from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from langchain.agents import create_agent, AgentState
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.messages import HumanMessage
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.checkpoint.memory import MemorySaver
from schemas.course_outline_schema import CourseOutline
import uuid
import json

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

# Build the system prompt dynamically
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
    
    prompt_parts.append("\nFormat the response in markdown with class titles as headings and bullet points for key topics under each class.")
    
    return "\n".join(prompt_parts)

async def run_graph(
    message: str, 
    topic: str = "", 
    number_of_classes: int = 1, 
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None
):
    """
    Run the LangChain agent with structured input and stream the results.
    
    Args:
        message: The main user message/prompt (optional additional context)
        topic: The topic/subject for the lesson plan
        number_of_classes: Number of classes in the lesson plan
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
        file_contents: Optional list of file contents with filename and content
    
    Returns:
        Generator that yields content chunks
    """
    try:
        # Use existing thread ID or create a new one
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Build the system prompt with all the context
        system_prompt = build_system_prompt(
            topic if topic else "general education",
            number_of_classes if number_of_classes > 0 else 1,
            file_contents
        )
        
        # Create a new agent instance with the dynamic system prompt and memory
        current_agent = create_agent(
            model=model,
            tools=tools,
            state_schema=CustomAgentState,
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


async def run_graph_structured(
    message: str, 
    topic: str = "", 
    number_of_classes: int = 1, 
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None
):
    """
    Run the LangChain agent with structured output using CourseOutline schema.
    Shows progress updates and returns the complete structured output at the end.
    
    Args:
        message: The main user message/prompt (optional additional context)
        topic: The topic/subject for the lesson plan
        number_of_classes: Number of classes in the lesson plan
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
        file_contents: Optional list of file contents with filename and content
    
    Returns:
        Generator that yields progress updates and structured data
    """
    try:
        # Use existing thread ID or create a new one
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Yield thread ID first
        yield {"type": "thread_id", "thread_id": thread_id}
        
        # Build the system prompt with all the context
        system_prompt = build_system_prompt(
            topic if topic else "general education",
            number_of_classes if number_of_classes > 0 else 1,
            file_contents
        )
        
        # Modify system prompt for structured output
        structured_prompt = system_prompt.replace(
            "Format the response in markdown with class titles as headings and bullet points for key topics under each class.",
            "Generate a structured course outline following the provided schema with detailed information for each class."
        )
        
        # Build the user prompt
        user_prompt_parts = []
        if message and message.strip():
            user_prompt_parts.append(message)
        user_prompt_parts.append(f"Create a comprehensive course outline for: {topic}")
        user_prompt_parts.append(f"Number of classes: {number_of_classes}")
        
        if file_contents and len(file_contents) > 0:
            user_prompt_parts.append("\nReference materials provided:")
            for file_info in file_contents:
                user_prompt_parts.append(f"- {file_info.get('filename', 'Unknown file')}")
        
        full_prompt = "\n".join(user_prompt_parts)
        
        # Yield progress update
        yield {"type": "progress", "message": "Generating course outline..."}
        
        # Use the model with structured output
        structured_model = model.with_structured_output(CourseOutline)
        
        messages = [
            {"role": "system", "content": structured_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        # Get the final complete structured output
        result = await structured_model.ainvoke(messages)
        
        # Convert to dict if it's a Pydantic model
        result_dict = result.model_dump() if isinstance(result, CourseOutline) else result
        
        # Yield the complete structured output
        yield {
            "type": "complete",
            "data": result_dict
        }
        
    except Exception as e:
        yield {"type": "error", "message": f"Error while generating structured content: {str(e)}"}