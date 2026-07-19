<div align="center">

# ⚽ FIFA World Cup 2026 — Smart Stadium Operations & Fan Experience Platform

### Challenge 4: Smart Stadiums & Tournament Operations

[![Challenge Vertical](https://img.shields.io/badge/Challenge-Smart%20Stadiums%20%26%20Tournament%20Ops-green?style=for-the-badge)](https://github.com)
[![Built With](https://img.shields.io/badge/AI-Google%20Gemini%20RAG-blue?style=for-the-badge)](https://ai.google.dev)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%202.0-009688?style=for-the-badge)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black?style=for-the-badge)](https://nextjs.org)
[![WCAG](https://img.shields.io/badge/Accessibility-WCAG%202.2%20AA-purple?style=for-the-badge)](https://www.w3.org/WAI/WCAG22)

</div>

---

## 🎯 Challenge Overview

**Challenge 4** requires a GenAI-enabled solution that enhances **stadium operations and the tournament experience** for fans, organizers, volunteers, and venue staff during the FIFA World Cup 2026.

This platform directly addresses **every required problem statement vertical**:

| Problem Statement Vertical | Implementation |
|---|---|
| 🗺️ **Navigation** | Dijkstra multi-criteria pathfinder with step-free accessible routing |
| 👥 **Crowd Management** | Real-time predictive density analytics with 15/30/60-minute forecasts |
| ♿ **Accessibility** | WCAG 2.2 AA+, TTS voice navigation, wheelchair-optimized routing |
| 🚌 **Transportation** | Live transit feed aggregator with AI-generated multilingual advisories |
| 🌱 **Sustainability** | Green impact calculator, gamified badges, location-aware eco nudges |
| 🌍 **Multilingual Assistance** | 5-language AI assistant (EN, ES, FR, AR, PT) with RAG grounding |
| 📊 **Operational Intelligence** | Async briefing engine, Prometheus metrics, Sentry error tracking |
| ⚡ **Real-Time Decision Support** | Human-in-the-loop safety copilot with RBAC incident approval workflow |

---

## 🧠 Approach & Architecture

### Chosen Approach: Clean Architecture + RAG-Grounded GenAI

The system is structured around three core principles:

1. **Grounded AI over Hallucination** — Every LLM call is anchored to verified database records. AI output is checked by `verify_output_grounding()` before serving fans.
2. **Human-in-the-Loop Safety** — Incidents are drafted by field staff, AI suggests responses, but **only authorized organizers** can broadcast approvals.
3. **Graceful Degradation** — When AI/network fails, the system falls back to pre-cached SOPs, rule-based translations, and offline PWA mode.

```
[ React Next.js 15 PWA ] <─── WebSocket / REST ───> [ FastAPI 2.0 Core ]
                                                             │
         ┌───────────────────────────────────────────────────┤
         │                 BACKEND LAYERS                    │
         ├────────────────┬───────────────┬──────────────────┤
         │  API ROUTERS   │ SERVICE LAYER │ REPOSITORY LAYER │
         │  app/api/      │ app/services/ │ app/repositories/│
         │  ─ auth.py     │ ─ llm.py      │ ─ stadium.py     │
         │  ─ assistant.py│ ─ ai_safety.py│   (all DB calls) │
         │  ─ crowd.py    │ ─ analytics.py│                  │
         │  ─ transport.py│ ─ route_opt.. │  DATABASE LAYER  │
         │  ─ decision.py │ ─ sustain..   │  app/database.py │
         │  ─ match.py    │ ─ match_sim.. │  SQLAlchemy ORM  │
         │  ─ ws.py       │               │  SQLite/Postgres  │
         └────────────────┴───────────────┴──────────────────┘
```

---

## 🧩 Feature Modules (Problem Statement Alignment)

### 1. 🗺️ Conversational Multilingual Assistant & Navigation (Navigation + Multilingual)

**What it solves**: Fans from 200+ nations need instant navigation in their native language.

**Implementation**:
- **PII Scrubbing** — Redacts phone numbers, emails, credit cards (`TKT-XXXX`) before any AI call.
- **Prompt Injection Defense** — Scans for `ignore previous instructions`, `system prompt` patterns and blocks them before LLM invocation.
- **RAG Context Retrieval** — Queries `wayfinding_nodes`, `transit_alerts`, `crowd_sensors`, `sop_rules` tables to ground the AI response.
- **Dijkstra Pathfinder Integration** — Routes computed programmatically; result injected into the LLM context so AI explains a *verified* path.
- **Output Grounding Verification** — `verify_output_grounding()` cross-references any location name in the AI response against the DB. Unverified locations are corrected or response confidence drops.
- **Fail-Safe Fallback** — If Gemini API fails or confidence < 0.60, returns a pre-cached offline response with known SOP data.
- **Languages**: English (en), Spanish (es), French (fr), Arabic (ar), Portuguese (pt).

**Files**: `backend/app/api/assistant.py`, `backend/app/services/llm.py`, `backend/app/services/ai_safety.py`

---

### 2. 👥 Crowd Flow Intelligence & Predictive Analytics (Crowd Management)

**What it solves**: Stadiums hosting 68,000+ fans need proactive congestion prevention.

**Implementation**:
- **Sensor Telemetry Ingestion** — `POST /api/crowd/update` accepts zone density readings (0–100%).
- **Predictive Analytics Engine** — `CrowdAnalyticsService` applies a differential flow model: `density + (entry_rate - exit_rate) × time` to compute 15m, 30m, and 60m density forecasts.
- **Tiered Alerts** — Low (<50%), Moderate (50-80%), High/Critical (>80%) with plain-language operational advisories.
- **AI-Generated Advisories** — Google Gemini generates dynamic coordinator notifications contextual to zone & density.
- **Real-Time Push** — Density updates broadcast to Organizer Dashboard via WebSockets (`/ws/updates`).

**Files**: `backend/app/api/crowd.py`, `backend/app/services/analytics.py`

---

### 3. ♿ Accessible Navigation Engine (Accessibility)

**What it solves**: Spectators with mobility limitations need step-free, verifiable routes.

**Implementation**:
- **Graph Construction** — Stadium precinct waypoints (`wayfinding_nodes`) form a weighted graph.
- **Dijkstra Multi-Criteria Optimizer** — `RouteOptimizer.find_optimal_route()` computes shortest path while filtering/penalizing non-accessible nodes.
- **4 Routing Modes**:
  - `fastest` — Minimizes transit time
  - `safest` — Avoids high-density crowd zones
  - `accessible` — Restricts path to nodes with `has_wheelchair_ramp=True` or `has_elevator=True`
  - `least_crowded` — Prioritizes low-density zones
- **WCAG 2.2 AA+ Frontend** — ARIA landmarks, live regions, keyboard navigation, high-contrast toggle, reduced motion support, TTS voice narration via Web Speech API.

**Files**: `backend/app/services/route_optimizer.py`, `frontend/components/AIAssistant/`

---

### 4. 🚌 Transport Coordination Assistant (Transportation)

**What it solves**: Fans must reach the stadium from multiple transit entry points — delays cause dangerous crowd surges.

**Implementation**:
- **Multi-Feed Aggregator** — Stores Subway/Metro, Shuttle Bus, and Parking Express status in `transit_alerts` table.
- **AI Advisory Generator** — Gemini condenses raw delay data into spectator-friendly multilingual notifications.
- **Real-Time Broadcast** — Transit updates pushed instantly to all connected fans via WebSockets.

**Files**: `backend/app/api/transport.py`

---

### 5. 🌱 Sustainability & Gamification Engine (Sustainability)

**What it solves**: FIFA's sustainability goals require engaging fans to reduce plastic waste and carbon emissions.

**Implementation**:
- **Location-Aware Nudges** — Maps gate location to nearest water refill station, recycling bin, and EV shuttle bay.
- **Impact Calculator** — `SustainabilityService.calculate_green_impact()`:
  - Plastic saved: `refills × 25g`
  - CO₂ reduced: `2.6 kg` per public transit trip + `0.08 kg` per refill bottle avoided
  - Green Score: weighted composite of eco-actions
- **Gamification Badges** — Unlocks *Hydration Hero*, *Zero Waste Advocate*, *Green Transport Pioneer*, *Eco MVP*
- **AI Nudge Generation** — Gemini crafts personalized 1-2 sentence encouragement per gate/language.

**Files**: `backend/app/api/sustainability.py`, `backend/app/services/sustainability.py`

---

### 6. 📊 Operational Intelligence Briefing Engine (Operational Intelligence)

**What it solves**: Command center staff need consolidated situational awareness across all feeds.

**Implementation**:
- **Async Celery Task** — `tasks.py` offloads heavy aggregation from the main thread using background workers.
- **Multi-Source Aggregation** — Combines active incidents, draft SOP approvals, crowd bottlenecks, transit delays, and match telemetry.
- **Prometheus Observability** — `fifa_http_requests_total` and `fifa_http_request_latency_seconds` metrics exposed at `/metrics`.
- **Sentry Error Tracking** — Captures unhandled exceptions with FastAPI integration.
- **Structured Logging** — Centralized JSON-format logger (`app/core/logging.py`) with request context.

**Files**: `backend/app/tasks.py`, `backend/app/main.py`, `backend/app/core/logging.py`

---

### 7. ⚡ Real-Time Safety Decision Support Copilot (Decision Support)

**What it solves**: Field staff need AI-assisted guidance; organizers need human oversight before public broadcasts.

**Implementation**:
- **DRAFT Logging** — Field volunteers submit reports via `POST /api/decision/report`. Incidents start as `DRAFT` — invisible to fans.
- **RAG SOP Matching** — AI matches incident description against `sop_rules` table records for grounded action plans.
- **Multi-Context Awareness** — Action plan incorporates crowd density, transit status, weather context, and historical gate incident count.
- **RBAC-Protected Approval** — `POST /api/decision/approve` enforces `organizer` or `admin` role via `RoleChecker`.
- **Live Broadcast** — On approval, status transitions to `active` and plan is pushed via WebSockets to Active Safety Broadcast Channel.

**Files**: `backend/app/api/decision.py`, `backend/app/core/dependencies.py`

---

### 8. 📡 Real-Time Dynamic Match Telemetry Engine

**What it solves**: Fans inside the stadium need a live synchronized scoreboard experience.

**Implementation**:
- **MatchSimulator** — Uses system clock intervals to generate smooth, consistent match minutes, possession %, shots, and pass accuracy.
- **Seed Synchronization** — All clients share the same 5-second seed so state is synchronized across browsers.
- **5-Second Auto-Ticker** — Fan Portal polls `/api/match/live` every 5 seconds for zero-page-refresh live updates.

**Files**: `backend/app/services/match_simulator.py`, `backend/app/api/match.py`

---

## 🔒 Security Implementation

| Control | Category | Implementation |
|---|---|---|
| **OAuth2 JWT (HS256)** | Authentication | 30-min access + 7-day refresh tokens; `app/core/security.py` |
| **Role-Based Access Control** | Authorization | `fan` / `volunteer` / `organizer` / `admin` roles enforced on all sensitive endpoints |
| **PII Scrubbing** | Data Privacy | Regex redaction of phone numbers, emails, credit cards, ticket IDs before AI forwarding |
| **Prompt Injection Defense** | AI Safety | Keyword blacklist scan on all user inputs before LLM invocation |
| **SQL Parameterization** | Injection Prevention | SQLAlchemy ORM parameterized bindings — zero raw SQL string concatenation |
| **Output Grounding Verification** | AI Hallucination | All AI responses cross-checked against DB node records before serving |
| **OWASP Security Headers** | Transport Security | `HSTS`, `CSP`, `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy` |
| **Rate Limiting** | DDoS Mitigation | 60 req/min per IP (Redis-backed; in-memory fallback) |
| **Sentry Error Tracking** | Observability | Production error capture with `send_default_pii=False` |
| **Fail-Safe Fallbacks** | Resilience | Offline SOP dictionary + rule-based translations when AI/network fails |

---

## ♿ Accessibility (WCAG 2.2 AA+)

| Feature | Implementation |
|---|---|
| **Semantic HTML Landmarks** | `<main id="main-content">`, `<nav>`, `<header>`, `<aside>`, `<article>` |
| **ARIA Live Regions** | `role="status"`, `aria-live="polite"` on all dynamic content updates |
| **ARIA Roles & Labels** | `role="tabpanel"`, `aria-labelledby`, `aria-selected` on all interactive tabs |
| **Skip Navigation** | `.skip-nav` link activates on first `Tab` keypress |
| **Keyboard Focus Visibility** | High-contrast `:focus-visible` outline on all buttons and inputs |
| **Voice TTS Navigation** | Web Speech API synthesis reads out navigation step instructions |
| **Reduced Motion** | `@media (prefers-reduced-motion: reduce)` disables all CSS animations |
| **High Contrast Toggle** | `.a11y-high-contrast` mode available for visually impaired users |
| **Color + Text Labels** | Density indicators always show text label (e.g., "High Density (85%)") not just color |
| **Contrast Ratio** | Text meets ≥ 4.5:1 (normal) and ≥ 3:1 (large text) WCAG requirements |

---

## 🧪 Testing

```bash
cd backend
pip install pytest pytest-cov httpx
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
```

| Test Category | Tests |
|---|---|
| Health & Root | `test_root_endpoint`, `test_health_check_endpoint` |
| AI Safety & RAG | PII redaction, prompt injection blocking, coordinate grounding, multilingual fallback |
| OAuth2 Auth | Token issuance, invalid credentials, registration, `/me` profile |
| RBAC Authorization | Volunteer blocked from organizer endpoints (403) |
| Assistant & Dijkstra | RAG query, route optimizer with `accessible` preference |
| Crowd Intelligence | Status listing, density update, predictive forecasting |
| Transport | Status listing, delay update with AI summary |
| Sustainability | Nudge API, impact calculator (refills + transit trips) |
| Match Telemetry | Live score, fixtures list, score update + broadcast |
| Decision Copilot | Full draft → AI suggestion → RBAC approval → broadcast workflow |

---

## 📡 API Reference

| Category | Method | Endpoint | Auth Required |
|---|---|---|---|
| Health | GET | `/` | No |
| Health | GET | `/health` | No |
| Auth | POST | `/api/auth/register` | No |
| Auth | POST | `/api/auth/token` | No |
| Auth | GET | `/api/auth/me` | Bearer Token |
| Match | GET | `/api/match/live` | No |
| Match | GET | `/api/match/fixtures` | No |
| Match | POST | `/api/match/update` | No |
| Assistant | POST | `/api/assistant/query` | No |
| Crowd | GET | `/api/crowd/status` | No |
| Crowd | POST | `/api/crowd/update` | No |
| Transport | GET | `/api/transport/status` | No |
| Transport | POST | `/api/transport/update` | No |
| Sustainability | GET | `/api/sustainability/nudge` | No |
| Decision | GET | `/api/decision/list` | No |
| Decision | POST | `/api/decision/report` | No |
| Decision | POST | `/api/decision/approve` | `organizer` / `admin` |
| Metrics | GET | `/metrics` | No |
| WebSocket | WS | `/ws/updates` | No |
| Docs | GET | `/docs` | No |

---

## 🛠️ Local Setup

```bash
# 1. Clone repository
git clone https://github.com/salman-momin08/fifa_wc.git
cd fifa_wc

# 2. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env       # Add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend setup
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3000` for the Fan Portal, `http://localhost:8000/docs` for the interactive Swagger API.

---

## ☁️ Deployment (Render)

```bash
# 1. Push to GitHub (single main branch)
git add .
git commit -m "feat: complete FIFA WC 2026 stadium operations platform"
git push origin main

# 2. On Render: New → Blueprint → connect repo
# render.yaml handles build + start commands automatically
```

---

## 📁 Project Structure

```
fifa_wc/
├── backend/
│   ├── app/
│   │   ├── api/            # Thin route handlers (auth, assistant, crowd, etc.)
│   │   ├── core/           # Config, constants, logging, security, exceptions
│   │   ├── repositories/   # Database access layer (StadiumRepository)
│   │   ├── schemas/        # Pydantic validation models (request + response)
│   │   ├── services/       # Business logic (AI safety, analytics, LLM, routing)
│   │   ├── database.py     # SQLAlchemy ORM models + DB initialization
│   │   ├── main.py         # FastAPI app, middleware, routers
│   │   ├── tasks.py        # Celery async background tasks
│   │   └── worker.py       # Celery worker entry point
│   ├── tests/
│   │   ├── conftest.py     # Shared pytest fixtures + isolated test DB
│   │   └── test_main.py    # 25+ comprehensive test cases
│   ├── pyproject.toml      # Black, Ruff, MyPy, isort config
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── components/         # React components (FanPortal, Header, AIAssistant, etc.)
│   ├── pages/              # Next.js pages
│   └── public/             # Static assets + service worker
├── SECURITY.md             # Security policies and vulnerability reporting
├── ACCESSIBILITY.md        # WCAG 2.2 AA compliance documentation
├── ARCHITECTURE.md         # Detailed system architecture decisions
├── DEPLOYMENT.md           # Render + Docker deployment guide
└── README.md               # This file
```

---

## 💡 Assumptions

1. **Precinct Coordinate Grid** — Waypoint nodes in `wayfinding_nodes` map to physical stadium gate and concourse coordinates; coordinates are seeded at DB init and verified before AI grounding.
2. **Network Resilience** — Under stadium cellular congestion, the system degrades to local rule-based SOP fallbacks and PWA offline cache (`sw.js`).
3. **Role Assignment** — Fan accounts are publicly self-serviceable; `volunteer`/`organizer` roles are assigned by administrators at accreditation time.
4. **Match Data** — Live match telemetry is simulated via `MatchSimulator` using system-clock seeds; production integration with official FIFA Data APIs follows the same interface contract.
5. **Language Detection** — Language is fan-selected (not auto-detected) to ensure deliberate accessibility choices.
