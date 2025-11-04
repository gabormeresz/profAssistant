"""
Course outline generator using structured output (new approach).
Returns validated Pydantic CourseOutline model with progress updates.
"""
from typing import Dict, List
from schemas.course_outline_schema import CourseOutline
from agent.common import (
    model, 
    build_system_prompt, 
    generate_thread_id
)


async def run_structured_course_outline_generator(
    message: str, 
    topic: str = "", 
    number_of_classes: int = 1, 
    thread_id: str | None = None,
    file_contents: List[Dict[str, str]] | None = None
):
    """
    Run the LangChain model with structured output using CourseOutline schema.
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
        thread_id = generate_thread_id(thread_id)
        
        # Yield thread ID first
        yield {"type": "thread_id", "thread_id": thread_id}
        
        # Build the system prompt with all the context
        system_prompt = build_system_prompt(
            topic if topic else "general education",
            number_of_classes if number_of_classes > 0 else 1,
            file_contents
        )
        
        # Add structured output instruction
        system_prompt += "\nGenerate a structured course outline following the provided schema with detailed information for each class."
        
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
            {"role": "system", "content": system_prompt},
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
