# Workspace Rules & Guidelines - FIFA World Cup 2026 Stadium Operations System

This directory houses guidelines to avoid GenAI hallucinations, ensure security boundaries, and govern code development in this workspace.

## 1. GenAI Behavior & Non-Hallucination Constraints
- **Anchoring**: Every LLM prompt must be anchored to verifiable static metadata (e.g., stadium map coordinates, transit routes, and official SOP documents). Do not allow the model to invent new gate numbers, transit lines, or security protocols.
- **Verification of Coordinates**: When the LLM suggests locations (e.g., wheelchair ramps, restrooms, first-aid stations), verify them against the local DB database tables.
- **Fail-Safe Fallbacks**: If the LLM call times out or fails under tournament crowd conditions, the system must degrade to a pre-cached offline dictionary of emergency procedures, key route checkpoints, and translations.

## 2. Security Boundaries
- **Input Filtering**: Redact PII (e.g., ticket serial numbers, phone numbers, individual user names) from queries before forwarding to external GenAI endpoints.
- **Prompt Injection Defense**: Treat all user chat input as untrusted. Restrict LLM prompts using XML tag markers (e.g., `<user_query>...</user_query>`) and instruct the system to ignore instruction-altering strings.
- **Parameterization**: Never build dynamic SQL strings using user input. Use SQLite's parameterized placeholders (`?` or `$named_param`) for all operations.

## 3. Accessibility Guarantees (WCAG 2.2 AA)
- Screen reader-ready HTML using semantic elements (`<nav>`, `<main>`, `<header>`, `<article>`) and appropriate `aria-*` tags.
- The default UI color scheme must pass the contrast checks (at least 4.5:1 for normal text, 3:1 for large text).
- Avoid relying on visual cues alone (e.g., color-coded density indicators must have textual labels, like "High Density (85%)" and accessible patterns).
