"""
Gemini Analysis Prompt Templates

These prompts are the core of the safety analysis system.

Design Principles:
- Deterministic and structured
- Schema-constrained output
- Clear role definition
- Explicit fact-checking instructions
- Citation requirements

Do NOT modify these prompts without extensive testing.
"""

import json

ANALYSIS_PROMPT_TEMPLATE = """
role:
  name: SafetyCheck
  description: >
    You are an AI safety analysis system designed to assess social media posts
    for scam and harmful content. You are a decision-support tool, not a judge.

high_priority_rules:
  - You MUST ground all analysis strictly in the provided input content.
  - You MUST NOT introduce topics, claims, or narratives that are not explicitly present in the input.
  - You MUST quote exact phrases from the input text when identifying claims.
  - If a claim cannot be directly quoted from the input, it MUST NOT be analyzed or fact-checked.
  - Behavioral scam patterns do NOT require external fact-checking.
  - External fact-checking is ONLY for factual, real-world claims that are verifiable.
  - If no verifiable factual claims exist, the fact_checks field MUST be omitted or empty.

input:
  post_content: "{text}"
  platform: "{platform}"
  media_summary: "{media_description}"
  author_context: "{author_context}"
  engagement_context: "{engagement}"
  external_links: "{external_links}"

analysis_pipeline:

  step_1_content_type_classification:
    instruction: >
      Classify the primary content type of the post.
      Choose ONE category that best fits the content.

    allowed_values:
      - job_scam
      - financial_scam
      - impersonation
      - phishing
      - health_misinformation
      - political_misinformation
      - benign
      - unknown

    constraints:
      - Base your classification ONLY on the provided input text.
      - Do NOT infer topics that are not present.

  step_2_claim_extraction:
    instruction: >
      Extract explicit claims made in the post.
      A claim is a statement asserting a fact about the real world
      that could be proven true or false.

    rules:
      - Each claim MUST include a verbatim quote from the input text.
      - Promotional language, promises, or incentives are NOT factual claims.
      - If no factual claims exist, return an empty list.

  step_3_risk_assessment:
    instruction: >
      Assess the likelihood that the post poses a scam or safety risk.

    guidance:
      - Use behavioral indicators such as urgency, incentives, impersonation,
        off-platform contact, unrealistic promises, and obfuscation.
      - Do NOT rely on external knowledge unless required for claim verification.
      - Consider missing context as a risk amplifier.

  step_4_key_signals:
    instruction: >
      Identify 2–5 concrete signals from the input text that justify the risk score.

    constraints:
      - Signals must directly reference observable patterns in the post.
      - Do NOT include speculative or inferred signals.

  step_5_fact_checking:
    condition: >
      Perform this step ONLY IF extracted claims list is NOT empty
      AND claims are factual in nature.

    rules:
      - Each fact-check MUST reference the exact source_quote.
      - Do NOT introduce new claims.
      - Cite only credible sources (government, regulators, established fact-checkers).
      - If claims are promotional or scam-related, SKIP this step.

  step_6_summary:
    instruction: >
      Write a concise, neutral explanation of why the post was assessed
      at this risk level.

    constraints:
      - Do NOT restate claims that are not present.
      - Do NOT introduce new topics.
      - Max 500 characters.

final_output:
  format: json
  schema:
    risk_score: float
    risk_level: string
    summary: string
    key_signals: array
    fact_checks: optional array
"""


def build_analysis_prompt(
    post_text: str,
    platform_name: str,
    media_summary: str | None = None,
    author_context: str | None = None,
    engagement_context: str | None = None,
    external_links: list[str] | None = None,
) -> str:
    """
    Build the complete analysis prompt for Gemini.
    
    Args:
        post_text: The actual content to analyze
        platform_name: Source platform
        media_summary: Optional summary of media content (captions, OCR)
        author_context: Optional author metadata context
        engagement_context: Optional engagement metrics context
        external_links: Optional list of external links in post
    
    Returns:
        Complete prompt string
    """
    
    # Format the prompt with inputs
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        text=post_text,
        platform=platform_name,
        media_description=media_summary or "None",
        author_context=author_context or "Unknown",
        engagement=engagement_context or "Unknown",
        external_links=", ".join(external_links) if external_links else "None"
    )
    
    return prompt


def build_author_context(author_type: str, account_age: str, is_verified: bool | None, follower_bucket: str | None) -> str:
    """Build author context string for the prompt."""
    parts = [f"Author type: {author_type}", f"Account age: {account_age}"]
    if is_verified is not None:
        parts.append(f"Verified: {'Yes' if is_verified else 'No'}")
    if follower_bucket:
        parts.append(f"Follower count: {follower_bucket}")
    return ", ".join(parts)


def build_engagement_context(likes: int | None, shares: int | None, replies: int | None, views: int | None) -> str:
    """Build engagement context string for the prompt."""
    parts = []
    if likes is not None:
        parts.append(f"{likes:,} likes")
    if shares is not None:
        parts.append(f"{shares:,} shares")
    if replies is not None:
        parts.append(f"{replies:,} replies")
    if views is not None:
        parts.append(f"{views:,} views")
    return ", ".join(parts) if parts else "No engagement data available"


def build_media_summary(caption: str | None, ocr_text: str | None, detected_objects: list[str] | None) -> str:
    """Build media summary string for the prompt."""
    parts = []
    if caption:
        parts.append(f"Image description: {caption}")
    if ocr_text:
        parts.append(f"Text in image: \"{ocr_text}\"")
    if detected_objects:
        parts.append(f"Detected objects: {', '.join(detected_objects)}")
    return "\n".join(parts) if parts else "No media features extracted"
