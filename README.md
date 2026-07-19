# FIFA World Cup 2026 - Stadium Operations & Fan Portal (v2.0 Enterprise Grade)

A production-grade, enterprise-scale stadium operations command and fan experience platform designed for the FIFA World Cup 2026. This system leverages Google Gemini (with anchored RAG context retrieval and safe offline fallbacks) alongside a real-time dynamic **MatchSimulator Engine** to provide real-time wayfinding, accessibility navigation, live match telemetry, crowd analytics & forecasting, transit intelligence, sustainability tracking, and human-in-the-loop safety incident response.

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
│   │   │   ├── match.py           # Real-time Match Telemetry API (/api/match/live, /api/match/fixtures)
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
│   │   │   ├── match_simulator.py # Real-time Dynamic Match Telemetry Engine (scores, possession, shots)
│   │   │   ├── route_optimizer.py # Dijkstra pathfinder (fastest, safest, accessible, least crowded)
│   │   │   └── sustainability.py  # Green Score, CO2 calculation, and badge engine
│   │   ├── database.py            # SQLAlchemy models (User, Incident, MatchCenter, WayfindingNode, etc.)
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
│   ├── components/
│   │   ├── AIAssistant/           # AI Assistant chat workspace with localStorage persistence
│   │   ├── FanPortal/             # Live Match Center, Transit & Safety Broadcast Channel
│   │   ├── VolunteerConsole/      # Field staff incident logger & SOP guidance
│   │   └── OrganizerDashboard/    # Command center, crowd telemetry & incident approval panel
│   ├── lib/
│   │   ├── api.js                 # Frontend API client
│   │   ├── useAuth.js             # Custom JWT authentication hook
│   │   ├── useWebSocket.js        # Custom WebSocket hook with auto-reconnection
│   │   └── db.js                  # IndexedDB offline storage helper
│   ├── public/
│   │   ├── manifest.json          # PWA manifest
│   │   └── sw.js                  # Service Worker for offline asset caching
│   └── Dockerfile                 # Frontend container definition
├── render.yaml                    # Render Blueprint specification for 1-click cloud deployment
├── docker-compose.yml             # Full production stack (Postgres, Redis, Celery, Prometheus, Grafana)
├── prometheus.yml                 # Prometheus metrics scraping configuration
├── ARCHITECTURE.md                # System topology, database schema & Traceability Matrix
├── FEATURES_AUDIT.md              # Core modules audit & verification specification
└── README.md                      # Setup and deployment guide
```

---

## API Endpoints Overview

| Category | Endpoint | Method | Description |
|---|---|---|---|
| **Auth** | `/api/auth/token` | POST | Authenticate user & issue OAuth2 JWT access/refresh tokens |
| **Auth** | `/api/auth/register` | POST | Register a new user (`fan`, `volunteer`, `organizer`, `admin`) |
| **Match** | `/api/match/live` | GET | Real-time dynamic match telemetry (scores, possession %, shots, capacity) |
| **Match** | `/api/match/fixtures` | GET | Upcoming stadium match fixtures & schedules |
| **Match** | `/api/match/update` | POST | Update live match score & broadcast over WebSockets |
| **Assistant**| `/api/assistant/query` | POST | Fan Q&A, RAG grounding, and Dijkstra route optimization |
| **Crowd** | `/api/crowd/status` | GET | Current crowd density sensors & 15/30/60m predictive forecasts |
| **Transport**| `/api/transport/status` | GET | Transit alert statuses and delay summaries |
| **Decision** | `/api/decision/report` | POST | Log safety incident (DRAFT status) |
| **Decision** | `/api/decision/approve` | POST | RBAC restricted (`organizer`/`admin`) incident approval & broadcast |
| **WebSocket**| `/ws/updates` | WS | Real-time push updates for match scores, transit delays, and safety alerts |

---

## Getting Started

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
cd backend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.
