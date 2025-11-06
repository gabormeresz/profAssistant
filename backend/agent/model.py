from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

# Setup model type
model_type = "openai:gpt-4o-mini"

# Setup LLM using init_chat_model
model = init_chat_model(model_type)