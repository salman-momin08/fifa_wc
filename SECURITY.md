# FIFA World Cup 2026 - Security & Safety Architecture Specification

## 🛡️ Executive Summary

This document specifies the enterprise security, privacy, role-based authorization, and AI safety controls implemented in the FIFA World Cup 2026 Stadium Operations & Fan Experience System.

---

## 🔐 1. Authentication & Authorization

### 1.1 OAuth2 JWT Bearer Tokens
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Access Token Expiry**: 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`).
- **Refresh Token Expiry**: 7 days (`REFRESH_TOKEN_EXPIRE_DAYS = 7`).
- **Token Claims**: Contains `sub` (username), `role` (`fan`, `volunteer`, `organizer`, `admin`), `exp`, and `type`.

### 1.2 Role-Based Access Control (RBAC)
The custom FastAPI dependency `RoleChecker(allowed_roles)` protects sensitive operational endpoints:

| Role | Access Level | Permitted Actions |
|---|---|---|
| **Fan** | Public (No Login) | View Fan Portal, ask AI assistant, view live transit & match telemetry |
| **Volunteer** | Staff Credentials | Log draft safety incidents, access Volunteer Console SOP guides |
| **Organizer** | Command Staff | Approve safety incidents, initiate emergency broadcasts, view crowd analytics |
| **Admin** | Superuser | Full system administration, user management, global configuration |

---

## 🤖 2. GenAI Safety & Non-Hallucination Controls

### 2.1 PII Scrubbing
Before forwarding any query to external GenAI endpoints, `AISafetyService.sanitize_user_input()` scrubs sensitive data using regex filters:
- **Phone Numbers**: Matches `+1-555-XXXX` and formats $\rightarrow$ `[REDACTED PHONE]`
- **Email Addresses**: Matches RFC 5322 emails $\rightarrow$ `[REDACTED EMAIL]`
- **Credit Cards**: Matches 16-digit card sequences $\rightarrow$ `[REDACTED CARD]`
- **Ticket Serials**: Matches `TKT-XXXX` serial numbers $\rightarrow$ `[REDACTED TICKET]`

### 2.2 Prompt Injection Censorship
Scans input queries for prompt hijacking patterns (`ignore previous instructions`, `system prompt`, `override rules`). If detected, the query is blocked before LLM execution:
- Output: `[System Censor: Potential Prompt Injection Attempt Blocked]`

### 2.3 RAG Context Retrieval & Grounding Verification
- **Retrieval**: Fetches verified database metadata from `wayfinding_nodes`, `transit_alerts`, `crowd_sensors`, and `sop_rules`.
- **Output Grounding**: `verify_output_grounding()` cross-references location names in generated responses against database node records. If unverified locations are mentioned, response confidence is lowered or replaced with a deterministic fallback response.

---

## 🌐 3. Web & Network Security

### 3.1 OWASP Security Headers
Every HTTP response is injected with security headers via `SecurityHeadersMiddleware`:
- `Content-Security-Policy`: `default-src 'self' ...`
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains`
- `X-Frame-Options`: `DENY`
- `X-Content-Type-Options`: `nosniff`
- `Referrer-Policy`: `strict-origin-when-cross-origin`
- `Permissions-Policy`: `geolocation=(), microphone=(), camera=()`

### 3.2 SQL Injection Defense
All database interactions use SQLAlchemy ORM parameterized query bindings (`?` or `$param`). Raw dynamic SQL concatenation is strictly prohibited.

### 3.3 Rate Limiting
`RateLimitMiddleware` enforces a sliding-window rate limit of **60 requests/minute per client IP** using Redis to protect endpoints from DoS attacks.
