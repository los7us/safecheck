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


SYSTEM_PROMPT = """You are SafetyCheck, an expert AI safety analyst specializing in detecting scams, misinformation, and harmful content in social media posts.

Your role is to:
1. Assess the risk that a post contains scam or harmful content
2. Provide clear, evidence-based explanations
3. Identify and fact-check specific claims when present
4. Cite credible sources for fact-checks

You are a decision-support tool, not a definitive authority. Your analysis helps users make informed decisions.

CRITICAL REQUIREMENTS:
- Always respond with valid JSON matching the specified schema
- Be specific about which signals inform your assessment
- Only fact-check when verifiable claims are present
- Always cite credible sources (government agencies, established fact-checkers, academic sources)
- Distinguish between speculation and factual claims
- Account for context and nuance

WHAT NOT TO DO:
- Do not make absolute judgments without evidence
- Do not fact-check opinions or subjective statements
- Do not cite unreliable sources
- Do not over-emphasize minor issues
- Do not ignore legitimate context that reduces risk"""


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
    
    prompt_parts = [
        "Analyze the following social media post for potential scam or harmful content.",
        "",
        "POST CONTENT:",
        f'"{post_text}"',
        "",
        f"PLATFORM: {platform_name}",
    ]
    
    if media_summary:
        prompt_parts.extend([
            "",
            "MEDIA CONTENT:",
            media_summary,
        ])
    
    if author_context:
        prompt_parts.extend([
            "",
            "AUTHOR CONTEXT:",
            author_context,
        ])
    
    if engagement_context:
        prompt_parts.extend([
            "",
            "ENGAGEMENT:",
            engagement_context,
        ])
    
    if external_links:
        prompt_parts.extend([
            "",
            "EXTERNAL LINKS:",
            "\n".join(f"- {link}" for link in external_links),
        ])
    
    prompt_parts.extend([
        "",
        "ANALYSIS INSTRUCTIONS:",
        "1. Assess the overall risk probability (0.0 to 1.0)",
        "2. Identify 2-5 specific signals that inform your assessment",
        "3. If verifiable factual claims are present, fact-check them",
        "4. For each fact-check, provide credible citations",
        "5. Write a concise summary explaining your assessment",
        "",
        "RESPONSE FORMAT:",
        "Respond with ONLY a JSON object matching this exact structure:",
    ])
    
    # Include the schema definition
    schema_example = {
        "risk_score": "float between 0.0 and 1.0",
        "risk_level": "one of: Minimal, Low, Moderate, High, Critical",
        "summary": "string, max 500 chars, concise explanation",
        "key_signals": ["list", "of", "2-5", "specific", "indicators"],
        "fact_checks": [
            {
                "claim": "specific claim being checked",
                "verdict": "one of: True, False, Misleading, Unverifiable, Lacks Context",
                "explanation": "string, max 500 chars",
                "citations": [
                    {
                        "source_name": "credible source name",
                        "url": "https://...",
                        "excerpt": "optional brief excerpt"
                    }
                ]
            }
        ]
    }
    
    prompt_parts.extend([
        json.dumps(schema_example, indent=2),
        "",
        "IMPORTANT:",
        "- Only include fact_checks if verifiable claims exist",
        "- Each fact-check must have 1-3 credible citations",
        "- Ensure risk_level matches risk_score ranges:",
        "  * Minimal: 0.0-0.25",
        "  * Low: 0.25-0.5",
        "  * Moderate: 0.5-0.7",
        "  * High: 0.7-0.9",
        "  * Critical: 0.9-1.0",
    ])
    
    return "\n".join(prompt_parts)


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


RETRY_PROMPT = """Your previous response did not match the required JSON schema.

Please respond with ONLY a valid JSON object. Do not include any markdown formatting, backticks, or explanatory text.

The JSON must exactly match this structure:
{
  "risk_score": <float 0.0-1.0>,
  "risk_level": "<Minimal|Low|Moderate|High|Critical>",
  "summary": "<string max 500 chars>",
  "key_signals": ["<string>", "<string>", ...],
  "fact_checks": [
    {
      "claim": "<string>",
      "verdict": "<True|False|Misleading|Unverifiable|Lacks Context>",
      "explanation": "<string max 500 chars>",
      "citations": [
        {
          "source_name": "<string>",
          "url": "<https://...>",
          "excerpt": "<string, optional>"
        }
      ]
    }
  ]
}"""
