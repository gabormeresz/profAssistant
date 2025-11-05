"""
Lesson plan generator using structured output.
Returns validated Pydantic LessonPlan model with progress updates.
"""
from typing import Dict, List
from langchain.agents import create_agent
from schemas.lesson_plan import LessonPlan
from schemas.course_class import CourseClass
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
class LessonPlannerAgentState(AgentState):
    topic: str
    number_of_classes: int
    file_contents: Optional[List[Dict[str, str]]]

# Define context for runtime data
@dataclass
class Context:
    thread_id: str

def generate_thread_id(thread_id: str | None) -> str:
    """Generate or return existing thread ID."""
    return thread_id if thread_id else str(uuid.uuid4())


async def run_structured_lesson_plan_generator(
        message: str,
        course_title: str,
        class_details: CourseClass,
        thread_id: str | None = None,
        file_contents: List[Dict[str, str]] | None = None

):
    """
    Run the LangChain model with structured output using LessonPlan schema.
    Shows progress updates and returns the complete structured output at the end.
    
    Args:
        message: The main user message/prompt (optional additional context)
        course_title: The title of the course
        course_class: The class information for the course
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
        
        # setup system prompt
        system_prompt = """
        You are a helpful educational assistant.
        """

        # Create a new agent instance with the dynamic system prompt and memory
        current_agent = create_agent(
            model=model,
            tools=tools,
            state_schema=LessonPlannerAgentState,
            context_schema=Context,
            system_prompt=system_prompt,
            checkpointer=memory
        )
        
        # Build the user prompt
        user_prompt = f"""
        Create a comprehensive lesson plan for an academic teacher based on the following course and class details.
        Course Title: {course_title}
        Class Number: {class_details.class_number}
        Class Title: {class_details.class_title}
        Learning Objectives: {', '.join(class_details.learning_objectives)}
        Key Topics: {', '.join(class_details.key_topics)}
        Activities/Projects: {', '.join(class_details.activities_projects)}
        Additional information: {message}
        Please structure the lesson plan according to the provided schema.
        You might use 
        You might use the following additional context if provided:
        """
        if file_contents and len(file_contents) > 0:
            user_prompt += "\nYou might use the following additional context if provided:\n"
            for file_info in file_contents:
                user_prompt += f"- {file_info.get('filename', 'Unknown file')}\n"

        # Yield progress update
        yield {"type": "progress", "message": "Generating course outline..."}
        
        # Use the model with structured output
        structured_model = model.with_structured_output(LessonPlan)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get the final complete structured output
        result = await structured_model.ainvoke(messages)
        
        # Convert to dict if it's a Pydantic model
        result_dict = result.model_dump() if isinstance(result, LessonPlan) else result
        
        # Yield the complete structured output
        yield {
            "type": "complete",
            "data": result_dict
        }
        
    except Exception as e:
        yield {"type": "error", "message": f"Error while generating structured content: {str(e)}"}
