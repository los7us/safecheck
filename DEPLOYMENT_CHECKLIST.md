# Deployment Checklist

## Pre-Deployment

### Code Quality
- [ ] All tests passing
- [ ] No console.log in production
- [ ] Documentation complete

### Security
- [ ] API keys in env vars
- [ ] .env in .gitignore
- [ ] CORS configured
- [ ] Rate limiting enabled

### Configuration
- [ ] Production .env ready
- [ ] Cache backend: Redis
- [ ] Logging configured

## Deployment

### Backend (Railway/Fly.io)
- [ ] Create account
- [ ] Connect repository
- [ ] Set environment variables
- [ ] Deploy
- [ ] Verify `/health`

### Frontend (Vercel)
- [ ] Import repository
- [ ] Set `NEXT_PUBLIC_API_URL`
- [ ] Deploy
- [ ] Test production URL

### Cache (Redis)
- [ ] Redis provisioned
- [ ] `REDIS_URL` configured
- [ ] `CACHE_TYPE=redis`

## Post-Deployment

- [ ] Frontend loads
- [ ] Analysis works
- [ ] Caching working
- [ ] Set up monitoring
- [ ] Track costs

## Rollback Plan

1. Check deployment logs
2. Verify environment variables
3. Roll back to previous version
4. Investigate and fix
