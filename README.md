# FIFA World Cup 2026 - Stadium Operations & Fan Portal (v2.0 Enterprise Grade)

A production-grade, enterprise-scale stadium operations command and fan experience platform designed for the FIFA World Cup 2026. This platform integrates Google Gemini AI (anchored with Retrieval-Augmented Generation and deterministic offline rule fallbacks) alongside a real-time **MatchSimulator Engine**, Dijkstra pathfinding, predictive crowd analytics, WebSockets real-time sync, and human-in-the-loop safety command workflows.

---

## 🏛️ System Architecture & Layered Design

The codebase follows **Clean Architecture** principles to separate concerns into distinct, testable layers:

```text
[ React Next.js PWA Client ] <── WebSockets / REST API ──> [ FastAPI Core ]
                                                              │
   ┌──────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────┐
   │                                                    BACKEND LAYERS                                                   │
   ├─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬───────────────────────────┤
   │       API ROUTERS           │       SERVICE LAYER         │      REPOSITORY LAYER       │      DATABASE LAYER       │
   │  (app/api/)                 │  (app/services/)            │  (app/repositories/)        │  (app/database.py)        │
   │  - auth.py                  │  - ai_safety.py             │  - stadium.py               │  - User                   │
   │  - assistant.py             │  - match_simulator.py       │    (Encapsulates DB calls   │  - Incident               │
   │  - crowd.py                 │  - route_optimizer.py       │     for nodes, SOPs,        │  - CrowdSensor            │
   │  - transport.py             │  - analytics.py             │     sensors, alerts, &      │  - TransitAlert           │
   │  - decision.py              │  - sustainability.py        │     user accounts)          │  - WayfindingNode         │
   │  - sustainability.py        │  - llm.py                   │                             │  - MatchCenter            │
   │  - match.py                 │                             │                             │  - MatchFixture           │
   │  - ws.py                    │                             │                             │                           │
   └─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴───────────────────────────┘
```

---

## 🧩 Detailed Feature Deep Dive: How Each Module Works

### 1. Conversational Multilingual Assistant & Wayfinder (F-01)
* **Purpose**: Provides fans with instant navigation instructions, accessibility directions, and stadium answers in 5 languages (English, Spanish, French, Arabic, Portuguese).
* **How It Works**:
  1. **PII Scrubbing**: Sanitizes input query using regex filters to redact phone numbers, email addresses, credit cards, and ticket serial numbers (`TKT-XXXX`).
  2. **Prompt Injection Censorship**: Scans for hijack keywords (`ignore previous instructions`, `system prompt`) and blocks malicious prompts before AI execution.
  3. **RAG Context Retrieval**: Queries `wayfinding_nodes`, `transit_alerts`, `crowd_sensors`, and `sop_rules` tables to retrieve matching context.
  4. **Dijkstra Pathfinding Integration**: If the query asks for directions (e.g. *"How to go from Transit Plaza to Gate B"*), the request is passed to `RouteOptimizer` to compute exact routing, transit modes, and ETAs.
  5. **LLM Execution & Verification**: Calls Google Gemini API (`gemini-1.5-flash`). The generated output is parsed by `verify_output_grounding()` to cross-reference location names against database node records. If unverified locations are detected, the confidence score drops and a safe fallback response is returned.
  6. **UI Persistence**: Chat sessions are stored in `localStorage` so chat histories, renamed titles, and messages persist across browser reloads.

### 2. Crowd Flow Intelligence & Predictive Analytics (F-02)
* **Purpose**: Monitors real-time crowd density percentages (0% to 100%) across stadium gates and generates 15, 30, and 60-minute predictive forecasts.
* **How It Works**:
  1. **Sensor Telemetry Ingestion**: Accepts zone density updates via `POST /api/crowd/update`.
  2. **Predictive Analytics Engine (`analytics.py`)**: Uses a linear-rate differential flow model (`current_density + (entry_rate - exit_rate) * delta_t`) to compute future density levels at 15m, 30m, and 60m intervals.
  3. **Advisory Generation**: Categorizes density into *Low* (<50%), *Moderate* (50-80%), and *High/Critical* (>80%), generating automated plain-language advisories.
  4. **Real-Time Push**: Broadcasts updated sensor data over WebSockets (`/ws/updates`) to instantly update the *Organizer Dashboard*.

### 3. Accessible Navigation Engine (F-03)
* **Purpose**: Ensures wheelchair users and spectators with limited mobility receive step-free routes checking ramps, elevators, and escalators.
* **How It Works**:
  1. **Graph Construction**: Builds an edge graph from physical stadium precinct waypoints (`wayfinding_nodes`).
  2. **Dijkstra Optimization (`route_optimizer.py`)**: Calculates shortest path while applying weight penalties to non-accessible nodes (stairs, high-density crowds).
  3. **Multi-Criteria Optimization**: Supports 4 routing preferences:
     - **Fastest**: Minimizes transit time.
     - **Safest**: Avoids high-density crowd zones and active incident gates.
     - **Accessible**: Restricts path exclusively to nodes with `has_wheelchair_ramp=True` or `has_elevator=True`.
     - **Least Crowded**: Prioritizes routes passing through low-density zones.

### 4. Transport Coordination Assistant (F-04)
* **Purpose**: Aggregates transit feed bulletins (Subway/Metro, Shuttle Buses, Parking Express) and alerts fans to delays or service suspensions.
* **How It Works**:
  1. Stores transit status logs in the `transit_alerts` table.
  2. Offers dynamic multilingual translation (`translate_fallback()`) into target fan languages.
  3. Pushes live transit status changes instantly to connected UI clients over WebSockets.

### 5. Sustainability & Gamification Engine (F-05)
* **Purpose**: Encourages eco-friendly fan behavior (water refills, recycling, public transit) through location-based nudges and impact tracking.
* **How It Works**:
  1. **Location-Aware Nudges**: Fetches nearest water refill stations, recycling bins, and EV shuttle bays relative to the fan's selected gate.
  2. **Impact Calculation (`sustainability.py`)**: Computes personalized metrics:
     - Plastic saved: `25 grams` per refill.
     - CO₂ reduction: `1,200 grams` per public transit trip.
     - Green Score: Weighted formula based on total eco-actions.
  3. **Gamification Badges**: Unlocks virtual badges (*Hydration Hero*, *Zero Waste Champion*, *Eco Traveler*) as fans log sustainable actions.

### 6. Operational Intelligence Briefing Engine (F-06)
* **Purpose**: Provides stadium organizers with dynamic executive summaries compiled from multi-source telemetry feeds.
* **How It Works**:
  1. **Async Celery Task (`tasks.py`)**: Offloads heavy aggregation processing from the main thread.
  2. Summarizes active incidents, draft SOP approvals, crowd bottlenecks, and transit delays into a concise operational briefing.

### 7. Real-Time Safety Decision Support Copilot (F-07)
* **Purpose**: Enables field staff to report incidents and provides organizers with AI-suggested SOP response plans before public broadcast.
* **How It Works**:
  1. **Draft Logging**: Field staff submit reports via `POST /api/decision/report`. Incidents start in `DRAFT` status and are **not** visible to fans.
  2. **SOP Matching**: RAG pipeline matches incident scenario descriptions against official database guidelines (`sop_rules`).
  3. **RBAC Restricted Approval**: Organizers review, edit, or authorize the action plan via `POST /api/decision/approve` (protected by `RoleChecker(["organizer", "admin"])`).
  4. **Live Broadcast**: Upon approval, status changes to `active`, and the plan is broadcasted via WebSockets to the public *Active Safety Broadcast Channel*.

### 8. Real-Time Dynamic Match Telemetry Engine
* **Purpose**: Simulates live match statistics (ticking minutes, possession %, shots, pass accuracy, stadium capacity) in real-time.
* **How It Works**:
  1. **MatchSimulator Service (`match_simulator.py`)**: Uses system clock interval seeds to compute smooth, dynamic match minutes (`76'`, `77'`, `78'`, ..., `90+2'`).
  2. **Dynamic Fluctuation**: Possession percentages, shots on goal, and capacity stats fluctuate realistically every 5 seconds.
  3. **Auto-Ticker UI**: The *Fan Portal* polls `/api/match/live` every 5 seconds to update the live match center without page refreshes.

---

## 🔒 Security & Safety Controls

| Safeguard | Implementation File | Function |
|---|---|---|
| **OAuth2 JWT Authentication** | `backend/app/core/security.py` | Issues 30-min access tokens & 7-day refresh tokens signed with HS256 algorithm |
| **Role-Based Access Control (RBAC)** | `backend/app/core/dependencies.py` | Enforces role checks (`fan`, `volunteer`, `organizer`, `admin`) on sensitive endpoints |
| **PII Scrubbing** | `backend/app/services/ai_safety.py` | Redacts phone numbers, emails, credit cards, and ticket serials |
| **Prompt Injection Censorship** | `backend/app/services/ai_safety.py` | Rejects prompt hijacking patterns before AI invocation |
| **SQL Injection Defense** | `backend/app/database.py` | Uses SQLAlchemy parameterized query bindings (`?` or `$param`) |
| **Output Grounding Verification** | `backend/app/services/ai_safety.py` | Cross-references AI outputs against database node records to block hallucinations |
| **OWASP Security Headers** | `backend/app/main.py` | Sets strict `CSP`, `HSTS`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy` |

---

## ♿ Accessibility (WCAG 2.2 AA+) Features

* **ARIA Landmarks & Live Regions**: Implements `<main id="main-content">`, `<nav>`, `<aside>`, `role="tabpanel"`, and `role="status"` with `aria-live="polite"` for screen reader announcements.
* **Skip Navigation Link**: Accessible keyboard shortcut link (`.skip-nav`) visible on initial Tab key press.
* **Keyboard Focus Visibility**: High-visibility `:focus-visible` offset outlines on all interactive buttons and inputs.
* **Web Speech API Text-to-Speech**: Integrated TTS synthesis allowing fans to hear voice navigation steps.
* **Reduced Motion & High Contrast**: Includes `@media (prefers-reduced-motion: reduce)` and color-blindness high contrast toggle mode (`.a11y-high-contrast`).

---

## 📡 API Endpoints Reference

| Category | Endpoint | Method | Request Payload / Params | Description |
|---|---|---|---|---|
| **Auth** | `/api/auth/token` | POST | `Form(username, password)` | Issue JWT access & refresh tokens |
| **Auth** | `/api/auth/register` | POST | `JSON(username, password, role)` | Register new user account |
| **Auth** | `/api/auth/me` | GET | `Bearer Token` | Fetch current user profile & role |
| **Match** | `/api/match/live` | GET | None | Get real-time dynamic match telemetry |
| **Match** | `/api/match/fixtures` | GET | None | Get upcoming stadium match fixtures |
| **Match** | `/api/match/update` | POST | `JSON(home_score, away_score, ...)` | Update match score & broadcast update |
| **Assistant**| `/api/assistant/query` | POST | `JSON(query, lang)` | Fan Q&A, RAG grounding & Dijkstra route |
| **Crowd** | `/api/crowd/status` | GET | None | Current sensors & 15/30/60m density forecasts |
| **Crowd** | `/api/crowd/update` | POST | `JSON(zone, density_percentage)` | Update sensor density & trigger alerts |
| **Transport**| `/api/transport/status` | GET | None | Fetch transit alerts & delay summaries |
| **Transport**| `/api/transport/update` | POST | `JSON(route, status, delay_minutes)` | Update transit feed & broadcast update |
| **Sustain.** | `/api/sustainability/nudge`| GET | `?gate=Gate A&lang=en` | Get location-aware eco nudges & score |
| **Decision** | `/api/decision/report` | POST | `JSON(title, description, gate, severity)` | Log safety incident (DRAFT status) |
| **Decision** | `/api/decision/approve` | POST | `JSON(incident_id, custom_action)` | RBAC restricted incident approval |
| **Decision** | `/api/decision/list` | GET | None | List active and draft incidents |
| **WebSocket**| `/ws/updates` | WS | None | Real-time WebSocket push updates |

---

## 🛠️ Setup & Deployment Guide

### Option A: 1-Click Cloud Deployment on Render (Recommended)
1. Push your repository to GitHub.
2. Sign in to your [Render Dashboard](https://dashboard.render.com) $\rightarrow$ **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository. Render will automatically read `render.yaml` and deploy the application.

### Option B: Local Docker Compose Stack
```bash
# Copy template configuration
cp backend/.env.example backend/.env

# Spin up full production container stack
docker-compose up --build
```

### Option C: Standalone Local Setup
```bash
# 1. Backend (FastAPI with SQLite fallback)
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend (Next.js)
cd frontend
npm install
npm run dev
```
