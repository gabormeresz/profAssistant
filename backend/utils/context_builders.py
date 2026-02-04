"""
Utility functions for building context and messages for LLM prompts.
Includes support for file contents, RAG, and vectorstore integration.

TODO: DELETE THIS FILE once lesson_plan_generator.py is migrated to use RAG.
      Currently only used by lesson_plan_generator.py (line 75).
      See course_outline/nodes.py for RAG implementation pattern.
"""

from typing import Dict, List


def build_file_contents_message(file_contents: List[Dict[str, str]]) -> str:
    """Build a message containing file contents."""
    message_parts = ["\n<<<REFERENCE_MATERIALS_BEGIN>>>"]
    for file_info in file_contents:
        filename = file_info.get("filename", "Unknown file")
        content = file_info.get("content", "")
        message_parts.append(
            f"\n<<<FILE_BEGIN:{filename}>>>\n{content}\n<<<FILE_END>>>"
        )
    message_parts.append("\n<<<REFERENCE_MATERIALS_END>>>")
    return "\n".join(message_parts)
