
from openai import AsyncOpenAI
import dotenv

dotenv.load_dotenv()

client = AsyncOpenAI()


async def prompt_enhancer(message: str, topic: str = "topic not specified", num_classes: int = 1) -> str:
    """
    Enhance the user prompt with additional context.

    Args:
        message: The main user message/prompt
        topic: The topic/subject for the course outline
        num_classes: Number of classes in the course outline
    
    Returns:
        Enhanced prompt string
    
    Raises:
        Exception: If enhancement fails
    """

    system_prompt = """You are a prompt wizard that improves user prompts for educational content generation.
The user is in the process of creating a course outline of a given topic.
Given the user's initial prompt and the educational topic, enhance the user's prompt to provide clearer instructions to the LLM.
Answer in a concise manner and only with the enhanced prompt, without any additional explanations."""
    
    # Construct a more detailed prompt from the structured data
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