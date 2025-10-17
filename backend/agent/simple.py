
from openai import AsyncOpenAI
import dotenv

dotenv.load_dotenv()

client = AsyncOpenAI()

async def run_llm(message: str, topic: str = "", number_of_classes: int = 1):
    """
    Run the agent with structured input.
    
    Args:
        message: The main user message/prompt
        topic: The topic/subject for the lesson plan
        number_of_classes: Number of classes in the lesson plan
    """
    # Construct a more detailed prompt from the structured data
    prompt_parts = [message]
    
    if topic:
        prompt_parts.append(f"Topic: {topic}")
    
    if number_of_classes > 1:
        prompt_parts.append(f"Number of classes: {number_of_classes}")
    
    full_prompt = "\n".join(prompt_parts)
    
    # Use AsyncOpenAI for proper async streaming
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an educational assistant that helps create lesson plans and educational content."},
                {"role": "user", "content": full_prompt}
            ],
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"Error while generating content: {str(e)}\n"