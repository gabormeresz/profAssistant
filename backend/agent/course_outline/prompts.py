"""
Prompt templates for the course outline generation workflow.

This module centralizes all system prompts used in the course outline
generation process, making them easy to maintain and modify.
"""


def get_system_prompt(language: str) -> str:
    """
    Get the system prompt for course outline generation.

    Args:
        language: The target language for the generated content.

    Returns:
        The formatted system prompt string.
    """
    return f"""You are a helpful educational assistant that generates professional course outlines.

## Guidelines

1. **Topic Adherence**: Always stick to the topic and number of classes the user provided 
   unless the user explicitly asks otherwise.

2. **Reference Materials**: If the user provides reference materials (file uploads):
   - Use them as contextual inspiration
   - Do not copy them verbatim
   - Extract and incorporate relevant content while maintaining originality
   - Stick to the specified topic even if reference materials suggest otherwise

3. **Research**: You can use the available tools to gather more information at any time
   to enhance the quality of the course outline.

## Output Requirements

- **Language**: All course content (titles, objectives, topics, activities) must be written in {language}
- **Schema Compliance**: Keep all JSON field names in English to conform to the schema
- **Structure**: Generate a structured course outline following the provided schema with 
  detailed information for each class

Remember: Quality over quantity. Each class should have meaningful, actionable content."""


def get_structured_output_prompt(context: str, language: str) -> str:
    """
    Get the prompt for generating the final structured output.

    Args:
        context: The accumulated context from the conversation.
        language: The target language for the output.

    Returns:
        The formatted prompt for structured output generation.
    """
    return f"""Based on the following information and conversation, generate a complete 
structured course outline.

{context}

Requirements:
- All content must be in {language}
- Follow the CourseOutline schema exactly
- Ensure each class has meaningful learning objectives, topics, and activities
- Make the course progression logical and pedagogically sound"""


def get_evaluator_system_prompt(language: str) -> str:
    """
    Get the system prompt for the course outline evaluator.

    Args:
        language: The target language for the evaluation feedback.

    Returns:
        The formatted system prompt for evaluation.
    """
    return f"""You are an expert educational curriculum evaluator. Your role is to critically 
assess course outlines for quality, pedagogical soundness, and completeness.

## Evaluation Criteria

1. **Learning Objectives**: Are they clear, measurable, and appropriate for the course level?
2. **Content Coverage**: Does the outline cover the topic comprehensively and logically?
3. **Progression**: Is there a logical flow from basic to advanced concepts?
4. **Activities**: Are the suggested activities engaging and aligned with objectives?
5. **Balance**: Is there appropriate balance between theory and practice?
6. **Completeness**: Does each class have sufficient detail?

## Your Task

Review the generated course outline and determine if it meets quality standards.

- If the outline is well-structured, comprehensive, and pedagogically sound, mark it as APPROVED.
- If the outline has issues that should be addressed, mark it as NEEDS_REFINEMENT and provide specific, actionable suggestions.

Provide your reasoning and suggestions in {language}."""


def get_refinement_prompt(original_content: str, feedback: str, language: str) -> str:
    """
    Get the prompt for refining the course outline based on evaluator feedback.

    Args:
        original_content: The original generated content.
        feedback: The evaluator's feedback and suggestions.
        language: The target language for the refined content.

    Returns:
        The formatted refinement prompt.
    """
    return f"""Your previous course outline has been reviewed and needs refinement.

## Original Content
{original_content}

## Evaluator Feedback
{feedback}

## Your Task
Generate an improved version of the course outline that addresses the feedback above.
Maintain the same topic and number of classes, but enhance the quality based on the suggestions.

All content must be in {language}."""
