"""
Shared prompt building blocks used across all generation workflows.

Centralizes the research-tools documentation and evaluation-context
formatting that would otherwise be duplicated in every workflow's
prompts.py.
"""

from __future__ import annotations


def build_research_tools_section(artifact_name: str, deliverables: str) -> str:
    """Build the research tools documentation block for system prompts.

    Args:
        artifact_name: What is being generated, e.g. "course outline".
        deliverables: Comma-separated list of expected output parts,
            e.g. "classes, objectives, topics, and activities".
    """
    return f"""## Available Research Tools

You have access to the following tools to gather information for building the {artifact_name}:

1. **tavily_search**: Search the web for current information, news, and real-world examples.
   - Use for: Recent developments, real-world applications, current examples

2. **tavily_extract**: Extract detailed content from specific web page URLs.
   - Use for: Reading full articles, getting detailed information from a known URL

3. **search_wikipedia**: Search Wikipedia for articles matching a query.
   - Use for: Discovering relevant articles, foundational concepts, background information
   - Best for: Finding the right article titles and overviews on a topic

4. **get_article**: Get the full content of a Wikipedia article by title.
   - Use for: Reading complete articles on key concepts, detailed explanations
   - Requires: An exact article title (use `search_wikipedia` first to find it)

5. **get_summary**: Get a concise summary of a Wikipedia article by title.
   - Use for: Quick overviews, definitions, background information
   - Requires: An exact article title (use `search_wikipedia` first to find it)

6. **search_uploaded_documents** (if documents uploaded): Search user's reference materials.
   - Use for: Aligning with existing curriculum, specific examples, preferred approaches

**Tool Usage Strategy**:
- Use `search_wikipedia` first to discover relevant articles, then `get_summary` or `get_article` for details
- Use `tavily_search` for current applications, recent developments, and practical examples
- Use `tavily_extract` to read detailed content from promising URLs found via search
- Use `search_uploaded_documents` to incorporate user's specific materials and preferences

**Responding to Explicit User Tool Requests**:
When the user explicitly asks you to search the web, look something up online, or use a specific tool — you MUST comply by calling the appropriate tool(s). Examples of such requests:
- "search the web", "look it up online", "keress rá a neten", "nézz utána az interneten" → use `tavily_search` with a relevant query about the topic
- "check Wikipedia", "look it up on Wikipedia" → use `search_wikipedia`
- "search my documents", "check my files", "nézd meg a fájljaimat" → use `search_uploaded_documents`
After using the requested tools, incorporate the findings into your generated content. Do NOT just return raw search results — always produce complete, well-structured educational content enriched by the research.

**CRITICAL — Tool Result Handling**:
Tools are supplementary research aids. Their results are INPUTS for your generation, never the output itself.
- **NEVER** output raw tool results, search summaries, lists of URLs, or external resource listings as your response
- **NEVER** output tool error messages (e.g. "article not found") as your response
- **NEVER** let a failed lookup prevent you from generating a complete {artifact_name}
- **ALWAYS** use tool results as background research to inform and enrich the {artifact_name} you generate
- If a tool fails or returns empty results, fall back to your own expert knowledge immediately
- Your output must ALWAYS be a complete, well-structured {artifact_name} with {deliverables} — regardless of tool availability or results"""


# ---------------------------------------------------------------------------
# Evaluation context helpers
# ---------------------------------------------------------------------------
# Each tuple: (display_label, score_breakdown_attribute, fix_description)
DimensionConfig = list[tuple[str, str, str]]


def build_eval_context(
    evaluation_history: list,
    dimensions: DimensionConfig,
) -> tuple[str, str]:
    """Build evaluation history context and focus instructions for refinement prompts.

    Args:
        evaluation_history: Evaluation objects with ``score``,
            ``score_breakdown``, ``reasoning``, and ``suggestions``.
        dimensions: Per-workflow dimension definitions — list of
            ``(display_label, attr_name, fix_description)`` tuples.

    Returns:
        ``(history_context, focus_instruction)`` ready to interpolate
        into the refinement prompt template.
    """
    history_context = ""
    for i, evaluation in enumerate(evaluation_history, 1):
        # Build dimension rows for the markdown table
        rows = ""
        for label, attr, _ in dimensions:
            score = getattr(evaluation.score_breakdown, attr)
            status = "✓" if score >= 0.8 else "✗ Needs work"
            rows += f"| {label} | {score:.2f} | {status} |\n"

        history_context += f"""
### Evaluation Round {i}
**Overall Score: {evaluation.score:.2f}** (Target: ≥ 0.80)

| Dimension | Score | Status |
|-----------|-------|--------|
{rows}
**Evaluator's Assessment:**
{evaluation.reasoning}

**Required Improvements:**
"""
        for j, suggestion in enumerate(evaluation.suggestions, 1):
            history_context += (
                f"{j}. [{suggestion.dimension.upper()}] {suggestion.text}\n"
            )

    # Build focus instruction from latest evaluation
    focus_instruction = ""
    latest = evaluation_history[-1] if evaluation_history else None
    if latest:
        weak_areas: list[tuple[str, float, str]] = []
        for label, attr, fix in dimensions:
            score = getattr(latest.score_breakdown, attr)
            if score < 0.8:
                weak_areas.append((label, score, fix))

        if weak_areas:
            focus_instruction = "\n## Priority Fixes (Dimensions Below 0.8)\n\n"
            for name, score, fix in sorted(weak_areas, key=lambda x: x[1]):
                focus_instruction += f"**{name}** ({score:.2f}): {fix}\n\n"

    return history_context, focus_instruction
