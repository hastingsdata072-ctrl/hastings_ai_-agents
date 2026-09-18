# Customer Support AI Agent
### Built with Amazon Bedrock AgentCore · Strands Agents · AWS Lambda · Amazon Nova 2 Lite

A production-deployed AI agent that handles real customer support workflows end-to-end — tracking orders, processing refunds, answering product and policy questions, calculating loyalty discounts, and browsing live web pages. Built on Amazon Bedrock AgentCore with long-term cross-session memory, a managed code execution sandbox, and a tool gateway backed by AWS Lambda.

---

## What it does

Customers interact with the agent in natural language. The agent selects the right tool for each request and handles it fully:

| Request type | How it's handled |
|---|---|
| Order tracking | Calls `get_order` / `get_customer_orders` via AgentCore Gateway → `order_tracker` Lambda |
| Refund processing | Calls `initiate_refund` / `check_refund_status` / `get_return_label` via Gateway → `refund_processor` Lambda |
| Product & policy questions | Retrieves from Amazon Bedrock Knowledge Base via `search_knowledge_base` |
| Loyalty discount calculation | Runs exact arithmetic in AgentCore Code Interpreter via `calculate_loyalty_discount` |
| Live web lookups | Browses in real time via AgentCore Browser |
| Repeat customers | Recalls name, preferences, and prior interactions via AgentCore Memory across sessions |

---

## Architecture

```
Customer (agentcore invoke)
        │
        ▼
BedrockAgentCoreApp
  └── Strands Agent (Amazon Nova 2 Lite)
        ├── search_knowledge_base    → Bedrock Knowledge Base
        ├── calculate_loyalty_discount → AgentCore Code Interpreter
        ├── browser                  → AgentCore Browser
        └── Gateway tools (MCP)
              ├── order_tracker λ   (get_order, get_customer_orders, get_customer)
              └── refund_processor λ (initiate_refund, check_refund_status, get_return_label)

  MemoryHook (Strands hook)
    ├── retrieve_customer_context → AgentCore Memory (on every user message)
    └── save_support_interaction  → AgentCore Memory (after every response)
```

See [architecture.md](./architecture.md) for full service roles and request flow.

---

## Stack

| Layer | Technology |
|---|---|
| AI runtime | Amazon Bedrock AgentCore (managed ASGI) |
| Agent framework | Strands Agents |
| Model | Amazon Nova 2 Lite (`global.amazon.nova-2-lite-v1:0`) |
| Tool gateway | AgentCore Gateway (MCP over streamable HTTP) |
| Tool runtime | AWS Lambda (Python 3.14) |
| Knowledge base | Amazon Bedrock Knowledge Base |
| Code execution | AgentCore Code Interpreter |
| Web browsing | AgentCore Browser |
| Long-term memory | AgentCore Memory (SEMANTIC + USER_PREFERENCE strategies) |
| Region | `us-east-1` |

---

## Repository layout

```
customer-support-ai-agent/
├── main.py                    # Agent entrypoint — all tools, hooks, and routing
├── architecture.md            # System diagram and service roles
├── pyproject.toml             # Dependencies (uv / pip)
├── LICENSE
│
├── lambda/
│   ├── order_tracker.py       # GET /orders and /customers routes
│   └── refund_processor.py    # initiate_refund, check_refund_status, get_return_label
│
├── infra/
│   └── lambda_schema.json     # Tool schema for the AgentCore Gateway
│
└── docs/
    ├── reflection.md          # Design decisions and production considerations
    └── test-evidence/         # Screenshots from all test scenarios
```

---

## Running locally

**Prerequisites**
- Python 3.14+ with `uv` installed
- AWS CLI configured (`us-east-1`)
- Amazon Bedrock AgentCore access enabled
- AgentCore Gateway, Knowledge Base, and Memory resources deployed

**Install dependencies**
```bash
uv sync
```

**Run a single turn locally**
```bash
uv run main.py '{"prompt": "Where is my order ORD-001?", "customer_id": "CUST-123", "session_id": "s1"}'
```

**Deploy to AgentCore**
```bash
agentcore deploy
```

**Invoke the deployed agent**
```bash
agentcore invoke '{"prompt": "I need a refund for ORD-002", "customer_id": "CUST-123", "session_id": "s2"}'
```

---

## Key engineering decisions

**Why Code Interpreter for loyalty discounts?**
The discount calculation involves flooring to the nearest 500 points and applying tier percentages in a specific order. LLMs produce subtly wrong results on multi-step arithmetic with rounding. Running the calculation in a deterministic sandbox eliminates that class of error entirely — a wrong loyalty discount is the kind of mistake a customer notices and escalates immediately.

**Why AgentCore Memory with hooks?**
The `MemoryHook` fires on every incoming message and after every response, making memory retrieval and storage invisible to the rest of the agent. The agent doesn't need to decide when to remember things — it just happens. This keeps the system prompt focused on behaviour rather than memory management instructions.

**Silent failure is a production risk.**
During development, the Knowledge Base and Browser tools failed silently — the agent apologised and fabricated plausible answers instead of erroring out. The root cause was missing IAM permissions on the execution role. The fix was a scoped inline policy. The lesson: graceful degradation that hides failures from operators is more dangerous than a visible error, especially at scale.

---

## Test scenarios covered

| # | Scenario | Tool used |
|---|---|---|
| 01 | Order tracking — CUST-123 asks about ORD-001 | Gateway → `order_tracker` |
| 02 | Refund processing — request refund for delivered order | Gateway → `refund_processor` |
| 03 | Knowledge base RAG — return policy question | `search_knowledge_base` |
| 04 | Cross-session memory — agent recalls name and preference in a new session | AgentCore Memory |
| 05 | Loyalty discount — Gold tier customer with 4,250 points | `calculate_loyalty_discount` |
| 06 | Live browser — agent browses a real URL on request | AgentCore Browser |

Screenshots for all scenarios are in `docs/test-evidence/`.

---

## License

Udacity Project License — see [LICENSE](./LICENSE)
