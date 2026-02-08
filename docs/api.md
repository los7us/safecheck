# API Documentation

Base URL: `http://localhost:8000`

## Endpoints

### POST /api/analyze

Analyze content for safety risks.

**Request:**
```json
{
  "url": "https://reddit.com/...",     // OR
  "text": "Content to analyze...",
  "platform_hint": "reddit"             // optional
}
```

**Response (200):**
```json
{
  "success": true,
  "cached": false,
  "data": {
    "risk_score": 0.75,
    "risk_level": "High",
    "summary": "Analysis summary...",
    "key_signals": ["Signal 1", "Signal 2"],
    "fact_checks": [{
      "claim": "Guaranteed returns",
      "verdict": "False",
      "explanation": "No guarantees in investing...",
      "citations": [{
        "source_name": "SEC.gov",
        "url": "https://...",
        "excerpt": "Warning signs..."
      }]
    }],
    "analysis_timestamp": "2025-02-08T12:00:00Z",
    "model_version": "gemini-flash-latest"
  }
}
```

**Errors:**
- `400`: Missing url or text
- `429`: Rate limit exceeded
- `500`: Analysis failed

---

### GET /health

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1707393600.0,
  "components": {
    "pipeline": "ok",
    "gemini": "ok",
    "cache": "ok"
  }
}
```

---

### GET /api/metrics

**Response:**
```json
{
  "cache": {"hit_rate": 0.67},
  "requests": {"total_requests": 15, "avg_latency_seconds": 2.5},
  "rate_limits": {"hourly": {"remaining": 90}},
  "gemini": {"total_requests": 15}
}
```

---

### DELETE /api/cache

Clear result cache.

**Response:**
```json
{"message": "Cache cleared"}
```

## Data Types

### RiskLevel
`Minimal` | `Low` | `Moderate` | `High` | `Critical`

### ClaimVerdict
`True` | `False` | `Misleading` | `Unverifiable` | `Lacks Context`

## Rate Limits

- Hourly: 100 requests (default)
- Daily: 1,000 requests (default)

Configure via `HOURLY_REQUEST_LIMIT` and `DAILY_REQUEST_LIMIT` env vars.
