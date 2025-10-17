from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Annotated, Any, Dict
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
import uuid

load_dotenv()

# Setup tools
serper = GoogleSerperAPIWrapper()
tool_search = Tool(
    name="web_search",
    func=serper.run,
    description="Useful for when you need more information from an online search"
)
tools = [tool_search]

# Setup LLM
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

# Define State
class State(BaseModel):
    messages: Annotated[list[Any], add_messages]
    topic: str
    number_of_classes: int

# Define the outline generator node
def node_outline_generator(state: State) -> Dict[str, Any]:
    system_message = "You are a helpful educational assistant."
    user_message = f"""
    Please create a course outline on '{state.topic}' with {state.number_of_classes} classes.
    You can use the available tools to gather more information any time.
    Format the response in markdown with class titles as headings and bullet points for key topics under each class.
    """

    messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
    messages += state.messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("generate_course_outline", node_outline_generator)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.add_edge(START, "generate_course_outline")
graph_builder.add_conditional_edges("generate_course_outline", tools_condition, {"tools": 'tools', "__end__": END})
graph_builder.add_edge("tools", "generate_course_outline")

# Compile the graph with memory
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

async def run_graph(message: str, topic: str = "", number_of_classes: int = 1, thread_id: str | None = None):
    """
    Run the LangGraph with structured input and stream the results.
    
    Args:
        message: The main user message/prompt (optional additional context)
        topic: The topic/subject for the lesson plan
        number_of_classes: Number of classes in the lesson plan
        thread_id: Optional thread ID for conversation continuity. If None, creates a new one.
    
    Returns:
        Generator that yields tuples of (content_chunk, thread_id)
    """
    try:
        # Use existing thread ID or create a new one
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Prepare messages - only add user message if provided
        messages = []
        if message and message.strip():
            messages.append(HumanMessage(content=message))
        
        # Create the initial state
        state = State(
            messages=messages,
            topic=topic if topic else "general education",
            number_of_classes=number_of_classes if number_of_classes > 0 else 1
        )
        
        # First, yield the thread_id as metadata (with a special marker)
        yield f"__THREAD_ID__:{thread_id}\n"
        
        # Stream events from the graph
        async for event in graph.astream_events(state, config=config, version="v2"):  # type: ignore
            kind = event.get("event")
            
            # Stream LLM tokens as they are generated
            if kind == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        yield content
                    
    except Exception as e:
        yield f"Error while generating content: {str(e)}\n"