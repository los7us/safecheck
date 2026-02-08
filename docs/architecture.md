# SafetyCheck Architecture

## System Overview

```
┌─────────────┐
│   Frontend  │  Next.js + TypeScript
│   (React)   │  Risk visualization, input forms
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────┐
│   FastAPI   │  REST API, caching, rate limits
│   Backend   │
└──────┬──────┘
       │
┌──────┴──────────────┐
│                     │
▼                     ▼
┌────────┐     ┌──────────┐
│Platform│     │  Gemini  │
│Adapters│     │    AI    │
└────────┘     └──────────┘
```

## Components

### Frontend (Next.js)
- **AnalysisInput**: URL/text input form
- **AnalysisModal**: Results display overlay
- **RiskScoreGauge**: Visual risk indicator
- **FactCheckCard**: Citation-rich fact-checks

### Backend (FastAPI)
- **Endpoints**: `/api/analyze`, `/health`, `/api/metrics`
- **Caching**: Memory (dev) or Redis (prod)
- **Rate Limiting**: Configurable hourly/daily limits

### Ingestion Pipeline
- Platform-specific adapters → CanonicalPost schema
- Media processing (OCR, captioning)
- Hash-based caching

### Gemini Service
- Multimodal prompt building
- Structured JSON response parsing
- Retry logic with exponential backoff

## Data Flow

```
1. User submits URL/text
2. Cache check (SHA-256 hash)
   └─ HIT → Return cached result
   └─ MISS → Continue
3. Platform adapter extracts content
4. Gemini analyzes CanonicalPost
5. Result cached & returned
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind |
| Backend | FastAPI, Pydantic |
| AI | Google Gemini Flash (Latest) |
| Cache | Redis / Memory |
| Media | Tesseract OCR |
