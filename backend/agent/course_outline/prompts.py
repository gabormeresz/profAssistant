"""
Prompt templates for the course outline generation workflow.

This module centralizes all system prompts used in the course outline
generation process, making them easy to maintain and modify.
"""


def get_system_prompt(language: str, has_ingested_documents: bool = False) -> str:
    """
    Get the system prompt for course outline generation.

    Args:
        language: The target language for the generated content.
        has_ingested_documents: Whether user has uploaded documents to search.

    Returns:
        The formatted system prompt string.
    """
    document_search_instruction = ""
    if has_ingested_documents:
        document_search_instruction = """

## IMPORTANT: Document Search Required

The user has uploaded reference documents. You MUST use the `search_uploaded_documents` tool 
BEFORE generating the course outline to extract relevant information from these documents.

- Search for key concepts, topics, and structure from the uploaded materials
- Use multiple queries if needed to cover different aspects of the topic
- Incorporate the retrieved information (when relevant) into your course outline
- This step is mandatory - do not skip it"""

    return f"""You are a helpful educational assistant that generates professional course outlines.

## Guidelines

1. **Topic Adherence**: Always stick to the topic and number of classes the user provided 
   unless the user explicitly asks otherwise.

2. **Reference Materials**: If the user provides documents (via search tool), follow these rules:
   - Use them as contextual inspiration
   - Do not copy them verbatim
   - Extract and incorporate relevant content while maintaining originality
   - Stick to the specified topic even if reference materials suggest otherwise

3. **Research**: You can use the available tools to gather more information at any time
   to enhance the quality of the course outline.{document_search_instruction}

## Output Requirements

- **Language**: All course content (titles, objectives, topics, activities) must be written in {language}
- **Schema Compliance**: Keep all JSON field names in English to conform to the schema
- **Structure**: Generate a structured course outline following the provided schema with 
  detailed information for each class

Remember: Quality over quantity. Each class should have meaningful, actionable content."""


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

## Scoring Rubric (0.0 to 1.0 for each dimension)

### Learning Objectives (learning_objectives)
- **0.9-1.0**: Clear, measurable, uses action verbs (Bloom's taxonomy), appropriate level
- **0.7-0.8**: Mostly clear but some objectives vague or not measurable
- **0.5-0.6**: Many objectives unclear or missing measurability
- **0.0-0.4**: Objectives missing, vague, or inappropriate

### Content Coverage (content_coverage)
- **0.9-1.0**: Comprehensive, covers all essential topics, well-organized
- **0.7-0.8**: Covers main topics but misses some important subtopics
- **0.5-0.6**: Significant gaps in coverage or poor organization
- **0.0-0.4**: Major topics missing or content is superficial

### Progression (progression)
- **0.9-1.0**: Excellent scaffolding, basic→advanced flow, clear prerequisites
- **0.7-0.8**: Generally good flow with minor sequencing issues
- **0.5-0.6**: Some topics out of order, unclear dependencies
- **0.0-0.4**: Random organization, no logical progression

### Activities (activities)
- **0.9-1.0**: Engaging, varied, aligned with objectives, appropriate for topic
- **0.7-0.8**: Good activities but some lack alignment or variety
- **0.5-0.6**: Generic activities, poor alignment with objectives
- **0.0-0.4**: Activities missing, inappropriate, or disconnected

### Completeness (completeness)
- **0.9-1.0**: Each class has detailed objectives, topics, activities, timing
- **0.7-0.8**: Most classes complete but some lack detail
- **0.5-0.6**: Several classes missing important elements
- **0.0-0.4**: Many classes incomplete or underdeveloped

## Scoring Guidelines

1. Score each dimension independently using the rubric above
2. Calculate overall score as weighted average (all dimensions equal weight)
3. **APPROVED**: Overall score >= 0.8
4. **NEEDS_REFINEMENT**: Overall score < 0.8
5. Provide 1-3 suggestions targeting the lowest-scoring dimensions

Provide your reasoning and suggestions in {language}."""


def get_refinement_prompt(
    original_content: str,
    evaluation_history: list,
    language: str,
) -> str:
    """
    Get the prompt for refining the course outline based on evaluation history.

    Args:
        original_content: The original generated content.
        evaluation_history: List of all previous evaluations with scores.
        language: The target language for the refined content.

    Returns:
        The formatted refinement prompt.
    """
    # Build evaluation history context
    history_context = ""
    for i, evaluation in enumerate(evaluation_history, 1):
        history_context += f"""
### Iteration {i} (Score: {evaluation.score:.2f})
- Learning Objectives: {evaluation.score_breakdown.learning_objectives:.2f}
- Content Coverage: {evaluation.score_breakdown.content_coverage:.2f}
- Progression: {evaluation.score_breakdown.progression:.2f}
- Activities: {evaluation.score_breakdown.activities:.2f}
- Completeness: {evaluation.score_breakdown.completeness:.2f}

Feedback: {evaluation.reasoning}

Suggestions:
"""
        for suggestion in evaluation.suggestions:
            history_context += f"- [{suggestion.dimension}] {suggestion.text}\n"

    # Get the latest evaluation for focus areas
    latest = evaluation_history[-1] if evaluation_history else None
    focus_areas = ""
    if latest:
        scores = [
            ("learning_objectives", latest.score_breakdown.learning_objectives),
            ("content_coverage", latest.score_breakdown.content_coverage),
            ("progression", latest.score_breakdown.progression),
            ("activities", latest.score_breakdown.activities),
            ("completeness", latest.score_breakdown.completeness),
        ]
        lowest = sorted(scores, key=lambda x: x[1])[:2]
        focus_areas = f"Focus especially on improving: {', '.join([f'{name} ({score:.2f})' for name, score in lowest])}"

    return f"""Your course outline has been evaluated and needs refinement to achieve a higher quality score.

## Current Content
{original_content}

## Evaluation History
{history_context}

## Your Task
Generate an improved version of the course outline that addresses the feedback above.
{focus_areas}

Target: Achieve an overall score of 0.8 or higher.
Maintain the same topic and number of classes, but enhance the quality based on the suggestions.

All content must be in {language}."""
