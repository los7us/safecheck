# Troubleshooting Guide

## Common Issues

### Backend Won't Start

**ModuleNotFoundError**
```bash
cd backend
pip install -r requirements.txt
```

**GEMINI_API_KEY not set**
```bash
cp .env.example .env
# Edit .env and add your API key
```

---

### Frontend Won't Start

**Module errors**
```bash
cd frontend
rm -rf node_modules && npm install
```

**CORS errors**
- Ensure backend running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

---

### Analysis Fails

**400 Bad Request**: Invalid input - ensure URL or text provided

**429 Rate Limit**: Wait for limit reset or increase limits in .env

**500 Server Error**: Check backend logs for Gemini API issues

---

### Cache Not Working

- View metrics: `curl http://localhost:8000/api/metrics`
- Check cache initialized in startup logs
- Verify TTL not expired (default 1 hour)

---

### High Costs

- Check cache hit rate in `/api/metrics`
- Increase `CACHE_TTL`
- Set lower `DAILY_TOKEN_LIMIT`

---

## Debugging

```bash
# Enable debug logs
LOG_LEVEL=DEBUG uvicorn src.main:app --reload

# Test health
curl http://localhost:8000/health

# Clear cache
curl -X DELETE http://localhost:8000/api/cache
```

## Getting Help

1. Check backend/browser console logs
2. Run `python scripts/test_e2e.py`
3. Create GitHub issue with error details
