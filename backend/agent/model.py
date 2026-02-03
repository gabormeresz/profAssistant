from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from config import LLMConfig

load_dotenv()

# Setup LLM using init_chat_model with config
model = init_chat_model(f"openai:{LLMConfig.DEFAULT_MODEL}")