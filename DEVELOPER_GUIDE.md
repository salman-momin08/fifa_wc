# FIFA World Cup 2026 - Developer Guide

## 💻 Developer Onboarding & Architecture Guide

Welcome to the FIFA World Cup 2026 Stadium Operations Core project. This guide covers local environment setup, architecture standards, directory layouts, and testing workflows.

---

## 🏗️ Architecture & Coding Standards

The backend is built using **Clean Layered Architecture**:

```text
API Routers (app/api/)
      ↓
Service Layer (app/services/)
      ↓
Repository Layer (app/repositories/)
      ↓
Database Models (app/database.py)
```

### Key Principles:
1. **Single Responsibility**: Every router handles HTTP requests; services contain business logic; repositories handle SQL queries.
2. **Strict Validation**: All incoming request bodies and outgoing responses use Pydantic models from `app/schemas/`.
3. **GenAI Anchoring**: AI outputs must be verified against database node records (`wayfinding_nodes`) before returning to clients.

---

## 🧪 Testing Workflows

Run the automated Pytest test suite:
```bash
cd backend
python -m pytest -v
```

### Test Coverage Highlights:
- **Auth & RBAC**: Test token generation, password verification, and 403 Forbidden role restrictions.
- **AI Safety & RAG**: PII scrubbing regexes, prompt injection blocking, and location verification checks.
- **Dijkstra Pathfinder**: Multi-criteria pathfinding tests (`fastest`, `safest`, `accessible`, `least_crowded`).
- **Match Telemetry**: Dynamic simulator minute updates, possession %, and score updates.
