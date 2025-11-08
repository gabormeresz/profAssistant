
from openai import AsyncOpenAI
from typing import Optional, Dict, Any, List
import dotenv

dotenv.load_dotenv()

client = AsyncOpenAI()


async def prompt_enhancer(
    message: str,
    context_type: str = "course_outline",
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enhance the user prompt with additional context.

    Args:
        message: The main user message/prompt
        context_type: Type of content being generated ("course_outline" or "lesson_plan")
        additional_context: Optional dict with context-specific fields:
            - For course_outline: topic, num_classes
            - For lesson_plan: topic (course_title), class_title, learning_objectives, 
              key_topics, activities_projects
    
    Returns:
        Enhanced prompt string
    
    Raises:
        Exception: If enhancement fails
    """
    
    # Set default additional_context if not provided
    if additional_context is None:
        additional_context = {}

    # Define system prompts for different contexts
    system_prompts = {
        "course_outline": """You are a prompt wizard that improves user prompts for educational content generation.
The user is in the process of creating a course outline of a given topic.
Given the user's initial prompt and the educational topic, enhance the user's prompt to provide clearer instructions to the LLM.
Answer in a concise manner and only with the enhanced prompt, without any additional explanations.""",
        
        "lesson_plan": """You are a prompt wizard that improves user prompts for educational content generation.
The user is in the process of creating a detailed lesson plan for a specific class.
Given the user's initial instructions and the lesson context (class title, learning objectives, topics, activities), 
enhance the user's prompt to provide clearer instructions to the LLM.
Answer in a concise manner and only with the enhanced prompt, without any additional explanations."""
    }
    
    # Get appropriate system prompt
    system_prompt = system_prompts.get(context_type, system_prompts["course_outline"])
    
    # Construct user prompt based on context type
    if context_type == "lesson_plan":
        topic = additional_context.get("topic", "topic not specified")
        user_prompt = f"I want to create a detailed lesson plan for a class in the course '''{topic}'''. "
        
        # Add additional context if provided
        if "class_title" in additional_context:
            user_prompt += f"\nClass Title: {additional_context['class_title']}. "
        if "learning_objectives" in additional_context:
            objectives = additional_context["learning_objectives"]
            if isinstance(objectives, list) and objectives:
                user_prompt += f"\nLearning Objectives: {', '.join(objectives)}. "
        if "key_topics" in additional_context:
            topics = additional_context["key_topics"]
            if isinstance(topics, list) and topics:
                user_prompt += f"\nKey Topics: {', '.join(topics)}. "
        if "activities_projects" in additional_context:
            activities = additional_context["activities_projects"]
            if isinstance(activities, list) and activities:
                user_prompt += f"\nActivities/Projects: {', '.join(activities)}. "
        
        user_prompt += f"\n\nMy initial instructions are: '''{message}'''. "
        user_prompt += "\nEnhance it to make it clearer for generating a comprehensive lesson plan."
    else:  # course_outline
        topic = additional_context.get("topic", "topic not specified")
        num_classes = additional_context.get("num_classes", 1)
        user_prompt = f"I want to create a course outline about '''{topic}''' that consists of {num_classes} classes. "
        user_prompt += f"My initial prompt is: '''{message}'''. "
        user_prompt += "Enhance it to make it clearer for generating a course outline."

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=200
    )
    
    enhanced = response.choices[0].message.content
    
    if not enhanced:
        raise Exception("Failed to enhance prompt")
    
    return enhanced.strip()