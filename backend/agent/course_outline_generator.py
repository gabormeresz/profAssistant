"""
Course outline generator using markdown streaming (original approach).
Streams content token-by-token in markdown format.
"""
from typing import Dict, List
from langchain.agents import create_agent
from agent.common import (
    model, tools, memory, 
    CustomAgentState, Context, 
    build_system_prompt, generate_thread_id
)


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
