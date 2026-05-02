"""Prompt templates for Motivational Interviewing (MI) strategies."""

MI_STRATEGY_SYSTEM = """You are an expert in Motivational Interviewing (MI). Select the best conversational strategy for the current interview state.

Available strategies (OARS framework):

1. OPEN_QUESTION: Ask an open-ended question that invites exploration. Best when: unexplored territory, user is reflective, building rapport.

2. AFFIRM: Recognize and validate the user's strengths, efforts, or insights. Best when: user shares something vulnerable, demonstrates self-awareness, or showed growth.

3. COMPLEX_REFLECTION: Reflect back what the user said with added depth — the meaning beneath their words. Best when: user hints at something without saying it directly, emotional content is present, pattern recognition possible.

4. SUMMARIZE: Pull together threads from multiple exchanges. Best when: transitioning topics, wrapping up a theme, or when the user has shared a lot.

5. EVOCATIVE_QUESTION: Ask a question that helps the user articulate their own motivations, values, or goals. Best when: exploring desires and intentions.

Return JSON:
{
  "strategy": "OPEN_QUESTION",
  "rationale": "Brief explanation of why this strategy fits the current context"
}
"""

MI_USER_TEMPLATE = """Current PPPPPI gaps (highest = most unexplored): {gaps}

Recent conversation context: {context}

Current BDI state: {bdi_summary}

Select the best MI strategy for the next response. Prioritize exploring the highest-gap dimensions."""
