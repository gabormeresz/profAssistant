"""
Utility functions for building context and messages for LLM prompts.
Includes support for file contents, RAG, and vectorstore integration.
"""
from typing import Dict, List


def build_file_contents_message(file_contents: List[Dict[str, str]]) -> str:
    """Build a message containing file contents."""
    message_parts = ["\n--- Beginning of Reference Materials ---"]
    for file_info in file_contents:
        filename = file_info.get("filename", "Unknown file")
        content = file_info.get("content", "")
        message_parts.append(f"\nFile: {filename}\n{content}")
    message_parts.append("--- End of Reference Materials ---")
    return "\n".join(message_parts)
