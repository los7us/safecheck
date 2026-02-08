# SafetyCheck - Multimodal Social Media Safety Analysis Platform

## Objective
A platform-neutral, multimodal safety analysis system that evaluates public social media posts for potential scam or harmful content.

## Scope (MVP - Phase 1)
- **Modalities**: Text + Metadata + Images
- **Platforms**: Minimum 2 adapters (Reddit + Twitter/X)
- **Analysis**: Gemini-powered multimodal reasoning
- **Output**: Risk score + explainable report + fact-checks with citations

## Non-Goals
- Private or encrypted content analysis
- User profiling or surveillance
- Platform ToS violations
- PII collection or storage

## Tech Stack
- **Backend**: Python 3.11+ (FastAPI)
- **Frontend**: Next.js 14+ with TypeScript
- **AI**: Google Gemini API (multimodal)
- **Cache**: Redis (optional for MVP)

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python src/main.py
```

### Frontend
```bash
cd frontend
pnpm install
cp .env.local.example .env.local
# Edit .env.local with backend URL
pnpm dev
```

## Project Status
- [x] Day 0: Setup
- [ ] Day 1: Architecture & Contracts
- [ ] Day 2: Platform Adapters
- [ ] Day 3: Media Pipeline
- [ ] Day 4: Gemini Analysis
- [ ] Day 5: Frontend UI
- [ ] Day 6: Integration & Caching
- [ ] Day 7: Testing & Deploy

## License
MIT (or specify your license)
