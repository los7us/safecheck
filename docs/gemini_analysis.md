# Gemini Analysis Documentation

## Overview

The Gemini service provides AI-powered safety analysis of social media posts.

## Flow

```
CanonicalPost -> Prompt Builder -> Gemini API -> Response Parser -> SafetyAnalysisResult
```

## Output Schema

```json
{
  "risk_score": 0.85,
  "risk_level": "High",
  "summary": "Brief explanation...",
  "key_signals": ["Signal 1", "Signal 2"],
  "fact_checks": [
    {
      "claim": "Specific claim",
      "verdict": "False",
      "explanation": "Why it's false",
      "citations": [{"source_name": "SEC", "url": "https://..."}]
    }
  ]
}
```

## Risk Levels

| Level | Score Range | Meaning |
|-------|-------------|---------|
| Minimal | 0.0-0.25 | Very low risk |
| Low | 0.25-0.5 | Minor concerns |
| Moderate | 0.5-0.7 | Significant concerns |
| High | 0.7-0.9 | Strong scam indicators |
| Critical | 0.9-1.0 | Extremely likely scam |

---

## Usage

```python
from src.services.gemini_service import GeminiService
from src.core.schemas import CanonicalPost, PlatformName

service = GeminiService(api_key="your_key")

post = CanonicalPost(
    post_id="123",
    post_text="Investment opportunity...",
    platform_name=PlatformName.REDDIT,
)

result = await service.analyze(post)
print(f"Risk: {result.risk_level.value}")
```

---

## Error Handling

If Gemini fails, a fallback result is returned:
- Risk score: 0.5 (neutral)
- Summary: Explains analysis was unavailable
- Recommends manual review

---

## Testing

```bash
# Unit tests
pytest tests/unit/test_gemini_service.py -v

# Integration (requires API key)
python scripts/test_gemini_analysis.py
```
