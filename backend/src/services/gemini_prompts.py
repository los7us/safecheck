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


# Vision Analysis Prompt Template
VISION_ANALYSIS_PROMPT = """
role:
  name: SafetyCheck Vision Analyzer
  description: >
    You are an AI safety analysis system that analyzes BOTH text content AND 
    images for scam and harmful content. You have multimodal vision capabilities.

high_priority_rules:
  - You MUST analyze BOTH the text content AND the image together.
  - You MUST examine visual elements carefully: logos, UI design, colors, layout.
  - You MUST identify visual manipulation tactics and fake interfaces.
  - Quote exact phrases from visible text in the image when identifying claims.
  - Visual indicators are equally important as textual ones.

input:
  post_content: "{text}"
  platform: "{platform}"
  author_context: "{author_context}"
  engagement_context: "{engagement}"
  external_links: "{external_links}"
  
  IMAGE_ANALYSIS_REQUIRED: >
    An image has been provided. You MUST analyze it for:
    - Fake UI elements or spoofed interfaces
    - Counterfeit logos or branding
    - Visual manipulation or deception tactics
    - Screenshot authenticity (real vs fabricated)
    - Text within the image (read and analyze it)
    - Color schemes and layouts common in scams
    - Urgency graphics or fake verification badges
    - Professional vs suspicious visual design

analysis_pipeline:

  step_1_visual_content_analysis:
    instruction: >
      First, describe what you see in the image.
      Identify any text, logos, UI elements, and overall composition.
    
    look_for:
      - Text visible in the image
      - Logos or brand elements
      - Interface elements (buttons, forms, notifications)
      - Color palette and visual style
      - Signs of image manipulation

  step_2_content_type_classification:
    instruction: >
      Classify the primary content type considering BOTH text and image.
      Choose ONE category that best fits.

    allowed_values:
      - job_scam
      - financial_scam
      - impersonation
      - phishing
      - health_misinformation
      - political_misinformation
      - benign
      - unknown

  step_3_risk_assessment:
    instruction: >
      Assess the likelihood that this post poses a scam or safety risk.
      Consider BOTH textual AND visual indicators.

    visual_indicators_to_check:
      - Fake website screenshots
      - Spoofed app or platform interfaces
      - Unrealistic profit/gain displays
      - Fake verification badges
      - Low-quality or manipulated images
      - Inconsistent UI elements
      - Too-good-to-be-true visuals

  step_4_key_signals:
    instruction: >
      Identify 2-5 concrete signals from BOTH the text AND the image that 
      justify the risk score.

    constraints:
      - Include at least one visual signal if the image contains suspicious elements
      - Quote text from the image when relevant
      - Reference specific visual elements you observed

  step_5_fact_checking:
    condition: >
      Only if verifiable factual claims exist in text OR image.

  step_6_summary:
    instruction: >
      Write a concise explanation referencing BOTH text and visual elements.
    constraints:
      - Max 500 characters
      - Mention key visual findings

final_output:
  format: json
  schema:
    risk_score: float (0.0 to 1.0)
    risk_level: string (Minimal/Low/Moderate/High/Critical)
    summary: string (reference both text and visual elements)
    key_signals: array (include visual signals)
    fact_checks: optional array
    
  risk_level_mapping:
    Minimal: "0.0-0.25"
    Low: "0.25-0.5"
    Moderate: "0.5-0.7"
    High: "0.7-0.9"
    Critical: "0.9-1.0"
"""


def build_vision_analysis_prompt(
    post_text: str,
    platform_name: str,
    author_context: str | None = None,
    engagement_context: str | None = None,
    external_links: list[str] | None = None,
) -> str:
    """
    Build analysis prompt for vision mode.
    
    This prompt instructs Gemini to analyze BOTH text AND image content.
    
    Args:
        post_text: The user-provided text context
        platform_name: Source platform
        author_context: Optional author metadata
        engagement_context: Optional engagement metrics
        external_links: Optional external links
    
    Returns:
        Complete vision analysis prompt
    """
    return VISION_ANALYSIS_PROMPT.format(
        text=post_text,
        platform=platform_name,
        author_context=author_context or "Unknown",
        engagement=engagement_context or "Unknown",
        external_links=", ".join(external_links) if external_links else "None"
    )

