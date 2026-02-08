# Deployment Guide

## Quick Deploy

### Backend: Railway

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Set environment variables:
   ```
   GEMINI_API_KEY=your_key
   CACHE_TYPE=redis
   ```
4. Add Redis service (auto-configures REDIS_URL)
5. Deploy

### Frontend: Vercel

1. Create account at [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Root directory: `frontend`
4. Set environment:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```
5. Deploy

---

## Docker Deployment

```bash
# Backend
cd backend
docker build -t safetycheck-backend .
docker run -d -p 8000:8000 --env-file .env.production safetycheck-backend

# Frontend
cd frontend
docker build -t safetycheck-frontend .
docker run -d -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://backend:8000 safetycheck-frontend
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

```bash
docker-compose up -d
```

---

## Post-Deployment

```bash
# Verify
curl https://your-backend/health
curl https://your-frontend

# Monitor
curl https://your-backend/api/metrics
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `GEMINI_API_KEY` | ✅ | - |
| `CACHE_TYPE` | ❌ | memory |
| `REDIS_URL` | ❌ | - |
| `HOURLY_REQUEST_LIMIT` | ❌ | 100 |
| `DAILY_REQUEST_LIMIT` | ❌ | 1000 |
