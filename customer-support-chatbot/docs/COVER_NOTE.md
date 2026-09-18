# Cover Note — Customer Support AI Agent

This submission presents a production-style AI customer support agent built on Amazon Bedrock AgentCore, along with a resubmission that directly addresses the three issues raised in the prior review.

---

## What was built

A multi-turn customer support chatbot that classifies incoming messages and handles each route end-to-end:

- **Bug reports** — collects description, reproduction steps, and environment over successive turns, then files a ticket via a Lambda-backed `create_bug_report` tool and returns the ticket ID to the customer
- **Platform questions** — answers order, shipping, returns, and payment queries grounded exclusively in the shop FAQ
- **Out-of-scope requests** — redirects to the human support line without fabricating answers

All routing, information-gathering behaviour, and grounding constraints are expressed in a single system prompt. The AgentCore managed harness supplies the agent loop, session memory, and tool execution layer.

---

## Resubmission: issues addressed

### 1. Gateway error handling

`main.py`'s `invoke()` entrypoint now isolates the Gateway interaction in its own nested `try/except` block, separate from the outer handler. Three distinct failure branches are covered:

- `except (ConnectionError, TimeoutError)` — returns a backend connectivity or timeout message
- `except Exception` (inner) — returns a general tool/Gateway failure message
- `except Exception` (outer) — returns a generic unexpected-error message for anything outside the Gateway block

All three branches return hardcoded, sanitized strings. No exception object, traceback, or environment variable is ever included in a user-facing response. The real exception is logged server-side via `logger.error(...)` for debugging.

**Testing performed:** `GATEWAY_URL` was temporarily set to an invalid value and the agent was invoked live. The agent returned the sanitized failure message with no raw exception text or secrets exposed (`screenshots/reviewer_fix_gateway_failure.png`). `GATEWAY_URL` was then restored and the same order-tracking request was re-run, confirming normal operation resumed (`screenshots/reviewer_fix_gateway_restored.png`, `session_id: sanity-check`).

**Known limitation:** the test exercised the general `except Exception` inner branch, not the `ConnectionError`/`TimeoutError`-specific branch. That branch is implemented but was not independently captured — inducing a real timeout rather than an invalid-URL failure would require additional test infrastructure. This is flagged here rather than overstated in the evidence.

---

### 2. Full-terminal invocation evidence

Three new screenshots (`reviewer_fix_gateway_failure.png`, `reviewer_fix_memory_session_a.png`, `reviewer_fix_memory_session_b.png`) are full-terminal captures showing the `agentcore invoke` command and its response in a single frame.

The six original test screenshots (`test1` through `test6`) remain in their original form and were not recaptured in this pass. If the requirement was intended to apply to all invocation evidence rather than only the resubmission items, those can be recaptured on request.

---

### 3. Cross-session memory verification

Memory persistence was tested using a fresh `customer_id` (`CUST-999`, "Marcus") with no prior history, eliminating any ambiguity from accumulated state on existing test customers:

- **Session A** (`session_id: clean-memory-A`): Marcus introduces himself and states a preference for detailed explanations
- **Session B** (`session_id: clean-memory-B`, different session, same `customer_id`, invoked afterward): the agent correctly recalls both the name and the stated preference without being prompted

The two captures carry different request IDs (`166c3e5e...` and `52da01c3...`), confirming these are independent invocations rather than a replayed response.

---

## Submission contents

| File / folder | Description |
|---|---|
| `src/main.py` | Updated agent code with Gateway error-handling fix |
| `config/system_prompt.txt` | Completed system prompt — primary deliverable |
| `reflection.md` | Written reflection on design decisions and production considerations |
| `data/harness-tests.json` | Full test suite covering all three routing scenarios |
| `screenshots/test1_order_tracking.png` – `test6_browser_tool_response.png` | Original test evidence |
| `screenshots/reviewer_fix_gateway_failure.png` | Gateway failure test (sanitized response) |
| `screenshots/reviewer_fix_gateway_restored.png` | Gateway restored, normal operation confirmed |
| `screenshots/reviewer_fix_memory_session_a.png` | Cross-session memory — Session A |
| `screenshots/reviewer_fix_memory_session_b.png` | Cross-session memory — Session B |
