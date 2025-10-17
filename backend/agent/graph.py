
from openai import AsyncOpenAI
import dotenv

dotenv.load_dotenv()

client = AsyncOpenAI()

async def run_agent(user_input: str):

    # Use AsyncOpenAI for proper async streaming
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"Error while chatting: {str(e)}\n"