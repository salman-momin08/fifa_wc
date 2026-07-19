# FIFA World Cup 2026 - Deployment & Infrastructure Guide

## 🚀 Overview

This document provides complete instructions for deploying the FIFA World Cup 2026 Stadium Operations Core platform across local development, Docker Compose production stack, and 1-click Render cloud deployment.

---

## 🛠️ Deployment Targets

### Target 1: 1-Click Render Cloud Deployment (Blueprint)
1. Push code to your GitHub repository.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Select your repository. Render will parse `render.yaml` and provision:
   - FastAPI Backend Web Service
   - Next.js Frontend Web Service
   - Managed PostgreSQL Database

### Target 2: Production Docker Compose Stack
```bash
# Clone repository
git clone https://github.com/salman-momin08/fifa_wc.git
cd fifa_wc

# Copy environment variables template
cp backend/.env.example backend/.env

# Build and start services in background
docker-compose up -d --build
```

#### Provisioned Stack Services:
- **Frontend PWA**: `http://localhost:3000`
- **FastAPI Core**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001`

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/stadium_ops` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `JWT_SECRET` | Secret key for signing tokens | `32-byte-hex-string` |
| `JWT_ALGORITHM` | Algorithm for token signatures | `HS256` |
| `GEMINI_API_KEY` | Google Gemini API key (optional) | `AIzaSy...` |
| `ALLOWED_ORIGINS` | Permitted CORS origin URLs | `http://localhost:3000` |
| `SENTRY_DSN` | Sentry error tracking DSN (optional) | `https://...` |
