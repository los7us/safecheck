# SafetyCheck

> AI-powered safety analysis for social media content

SafetyCheck analyzes social media posts for scams, misleading claims, and harmful content using Google's Gemini AI. It provides explainable risk assessments with fact-checked citations.

Features

- Multi-Platform: Analyze Reddit, Twitter, and pasted text
- Multimodal: Evaluates text, images, and metadata
- Risk Scoring: Clear levels from Minimal to Critical
- Fact-Checking: Verifies claims with citations
- Fast & Cached: Results cached to reduce costs
- Responsive: Works on mobile, tablet, desktop

Tech stack: python(FastAPI) backend, next.js(typescript)

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Gemini API key](https://makersuite.google.com/app/apikey)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.template .env
# Edit .env and add GEMINI_API_KEY

uvicorn src.main:app --reload
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.template .env.local

npm run dev
# → http://localhost:3000
```

### Quick Test

1. Open http://localhost:3000
2. Paste: `URGENT! Send Bitcoin for guaranteed 10x returns!`
3. Click "Analyze Content"
4. View risk assessment

## 📖 Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🧪 Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run build
```

## 📊 Performance

| Metric | Target |
|--------|--------|
| Analysis latency | <5s |
| Cache hit latency | <100ms |
| Cost per analysis | <$0.01 |

Disclaimer

SafetyCheck is a decision-support tool. Always exercise your own judgment.

## License

MIT License
