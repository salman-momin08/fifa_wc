# FIFA World Cup 2026 - Stadium Operations & Fan Portal (v2.0 Enterprise Grade)

A production-grade, enterprise-scale stadium operations command and fan experience platform designed for the FIFA World Cup 2026. This system leverages Google Gemini (with anchored RAG context retrieval and safe offline fallbacks) to provide real-time wayfinding, accessibility navigation, crowd analytics & forecasting, transit intelligence, sustainability tracking, and human-in-the-loop safety incident response.

---

## Project Structure

```text
Fifa_Wc/
├── .agents/
│   └── AGENTS.md                  # GenAI non-hallucination rules & security boundaries
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline (tests, lint, Docker build)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── assistant.py       # Fan Q&A, RAG grounding & Dijkstra route optimizer
│   │   │   ├── auth.py            # JWT Authentication & user registration
│   │   │   ├── crowd.py           # Crowd telemetry & 15/30/60m density forecasting
│   │   │   ├── decision.py        # Safety incident copilot & RBAC approvals
│   │   │   ├── sustainability.py   # Green Score calculator & station locator
│   │   │   ├── transport.py       # Transit alerts aggregator
│   │   │   └── ws.py              # Real-time WebSocket connection manager (`/ws/updates`)
│   │   ├── core/
│   │   │   ├── dependencies.py    # OAuth2 Bearer extraction & RBAC RoleChecker
│   │   │   └── security.py        # PyJWT token encoding/decoding & bcrypt hashing
│   │   ├── repositories/
│   │   │   └── stadium.py         # Repository layer encapsulating SQL query logic
│   │   ├── schemas/
│   │   │   ├── assistant.py       # Assistant Pydantic schema with confidence & sources
│   │   │   ├── auth.py            # User registration, login, and token models
│   │   │   ├── crowd.py           # Crowd sensor update/output schemas
│   │   │   ├── incident.py        # Incident report/approval schemas
│   │   │   └── transport.py       # Transit alert schemas
│   │   ├── services/
│   │   │   ├── ai_safety.py       # RAG context, PII scrub, injection check & grounding
│   │   │   ├── analytics.py       # Predictive crowd flow density calculator
│   │   │   ├── llm.py             # Gemini API client & offline rules engine
│   │   │   ├── route_optimizer.py # Dijkstra pathfinder (fastest, safest, accessible, least crowded)
│   │   │   └── sustainability.py  # Green Score, CO2 calculation, and badge engine
│   │   ├── database.py            # SQLAlchemy models (User, Incident, WayfindingNode, etc.)
│   │   ├── main.py                # FastAPI app, security headers, rate limiter & Prometheus metrics
│   │   ├── tasks.py               # Celery async background tasks (briefs & notifications)
│   │   └── worker.py              # Celery app initialization with Redis broker
│   ├── tests/
│   │   └── test_main.py           # Comprehensive unit and integration test suite
│   ├── .env.example               # Environment variables template
│   ├── Dockerfile                 # Backend container definition
│   └── requirements.txt           # Python requirements
├── frontend/
│   ├── app/
│   │   ├── layout.js              # Global app frame & PWA manifest link
│   │   ├── page.js                # Multi-role dashboard with WebSocket real-time updates
│   │   ├── globals.css            # WCAG high-contrast, skip-nav & accessibility styles
│   │   └── SWRegister.js          # Service Worker registration client component
│   ├── lib/
│   │   ├── api.js                 # Frontend API client
│   │   ├── useAuth.js             # Custom JWT authentication hook
│   │   ├── useWebSocket.js        # Custom WebSocket hook with auto-reconnection
│   │   └── db.js                  # IndexedDB offline storage helper
│   ├── public/
│   │   ├── manifest.json          # PWA manifest
│   │   └── sw.js                  # Service Worker for offline asset caching
│   └── Dockerfile                 # Frontend container definition
├── docker-compose.yml             # Full production stack (Postgres, Redis, Celery, Prometheus, Grafana)
├── prometheus.yml                 # Prometheus metrics scraping configuration
├── ARCHITECTURE.md                # System topology, database schema & Traceability Matrix
├── FEATURES_AUDIT.md              # Core modules audit & verification specification
└── README.md                      # Setup and deployment guide
```

---

## Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (optional for containerized deployment)

---

### Option A: Running with Docker Compose (Recommended)

1. Copy environment configuration:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Launch the full production stack:
   ```bash
   docker-compose up --build
   ```

#### Services Available:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI API Core**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`
- **Prometheus Metrics**: `http://localhost:9090`
- **Grafana Dashboard**: `http://localhost:3001`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### Option B: Local Standalone Setup (Without Docker)

#### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*Note: If `DATABASE_URL` is unset, the backend automatically falls back to an embedded SQLite database (`stadium_ops.db`).*

#### 2. Running Backend Test Suite
```bash
pytest -v
```

#### 3. Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## Key Enterprise Upgrades Verified

### Gate 1: Code Quality & Clean Architecture
- **Layered Architecture**: Strict separation between API Routers, Service logic, Repository DB queries, and Pydantic Schemas.
- Full type annotations throughout Python & JavaScript codebases.

### Gate 2: Security, Authentication & Injection Blockers
- **JWT & RBAC**: OAuth2 password bearer flow with bcrypt password hashing. Roles (`fan`, `volunteer`, `organizer`, `admin`) enforce endpoint authorization.
- **PII Scrubbing & Prompt Injection**: Scans input for ticket serials, credit cards, emails, and phone numbers. Rejects prompt hijacking patterns before AI invocation.
- **Human-in-the-Loop SOPs**: Incident reports logged by field staff start in `DRAFT` status and require explicit `organizer`/`admin` approval before broadcast.
- **Security Headers**: Standard OWASP security headers (`CSP`, `HSTS`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`).

### Gate 3: High-Crowd Efficiency, Real-Time & Fallbacks
- **WebSockets (`/ws/updates`)**: Instant real-time push updates for crowd density changes, transit delays, and safety incident approvals (replacing client polling).
- **Distributed Rate Limiting**: Redis-backed rate limiter (60 req/min) with in-memory fallback.
- **Offline Resilience & PWA**: PWA shell with Service Worker (`sw.js`) and local offline lookup dictionaries for wayfinding and SOPs under dense crowd conditions.

### Gate 4: Observability & Background Jobs
- **Metrics & Sentry**: Integrated Prometheus counter/histogram metrics (`/metrics`) and Sentry error tracking.
- **Async Workers**: Celery app with Redis broker for background operations summary compilation and notification dispatch.

### Gate 5: Accessibility (WCAG 2.2 AA+)
- ARIA landmarks, `aria-live` announcement region for screen readers, keyboard focus indicators, skip-to-content link (`.skip-nav`), and prefers-reduced-motion support.
- Native browser Web Speech API text-to-speech (TTS) voice navigation.

### Gate 6: Traceability
- Full traceability matrix maintained in [ARCHITECTURE.md](file:///c:/Users/kmomin/OneDrive%20-%20Adobe/Desktop/Fifa_Wc/ARCHITECTURE.md).
