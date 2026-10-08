# NovaMart Multi-Agent Support System
### Built with Strands Agents · Amazon Bedrock AgentCore · Claude Haiku 4.5 + Sonnet 4.5 · DynamoDB · Bedrock Knowledge Bases

A production-grade multi-agent customer support system that automatically routes requests to specialist agents, retrieves grounded knowledge via parallel multi-agent RAG, enforces enterprise safety guardrails, and maintains shared workflow state — all observable through CloudWatch and AWS X-Ray.

---

## What it does

A customer sends one message. The system classifies it, routes it through the right combination of specialist agents, and returns a single coherent response. No manual routing. No hardcoded rules.

| Request type | Routing path |
|---|---|
| Order status / return / refund | Orchestrator → Inventory → Refund → Communication |
| Policy question (returns, shipping, warranty) | Orchestrator → Policy (3 parallel KB retrievers) → Communication |
| Calculation | Orchestrator → Communication (direct, no data lookup needed) |

---

## Architecture

```
Customer Request
      │
OrchestratorAgent  (Claude Haiku 4.5 — routes, manages WorkflowState)
      │
   ┌──┼───────────────────────────┬──────────────────────┐
   │  │                           │                      │
InventoryAgent    PolicyAgent    RefundAgent    CommunicationAgent
(DynamoDB)     (Multi-Agent RAG)  (DynamoDB)     (final response)
                     │
         ┌───────────┼───────────┐
  ReturnsPolicyRetriever  ShippingPolicyRetriever  WarrantyPolicyRetriever
  (Bedrock KB)            (Bedrock KB)             (Bedrock KB)
         └───────── run in PARALLEL ───────────┘

Shared State: DynamoDB WorkflowStateTable (optimistic locking)
Observability: AWS X-Ray traces + CloudWatch Logs
Safety: Bedrock Guardrails (content, PII, topic blocking)
```

See [architecture.md](./architecture.md) for full service roles, request flow, and design decisions.

---

## Agent roles

| Agent | Model | Responsibility |
|---|---|---|
| OrchestratorAgent | Claude Haiku 4.5 | Routes requests, creates/updates WorkflowState, never writes final response |
| InventoryAgent | Claude Sonnet 4.5 | Retrieves order and customer facts from DynamoDB — data only, no decisions |
| PolicyAgent | Claude Sonnet 4.5 | Coordinates 3 parallel KB retriever sub-agents, synthesizes grounded policy answer |
| RefundAgent | Claude Sonnet 4.5 | Makes return/refund eligibility decisions (30-day Standard, 60-day Premium window) |
| CommunicationAgent | Claude Sonnet 4.5 | Drafts final customer-facing response from accumulated WorkflowState |
| ReturnsPolicyRetriever | Claude Sonnet 4.5 | Queries Returns Knowledge Base |
| ShippingPolicyRetriever | Claude Sonnet 4.5 | Queries Shipping Knowledge Base |
| WarrantyPolicyRetriever | Claude Sonnet 4.5 | Queries Warranty Knowledge Base |

---

## Stack

| Layer | Technology |
|---|---|
| Agent framework | Strands Agents SDK |
| AI runtime | Amazon Bedrock AgentCore (managed runtime) |
| Orchestrator model | Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) |
| Worker models | Claude Sonnet 4.5 (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`) |
| Shared state | Amazon DynamoDB (WorkflowStateTable, optimistic locking) |
| Knowledge bases | Amazon Bedrock Knowledge Bases × 3 (S3 Vectors backing store) |
| Safety | Amazon Bedrock Guardrails (content filtering, PII redaction, topic blocking) |
| Memory | AgentCore Memory (SESSION_SUMMARY strategy, 7-day retention) |
| Observability | AWS X-Ray + Amazon CloudWatch Logs |
| Infrastructure | AWS CloudFormation |
| Deployment | AgentCore CLI (`@aws/agentcore` v0.30.0) |
| Region | `us-east-1` |

---

## Repository layout

```
novamart-multi-agent-support/
├── README.md
├── architecture.md
├── config.py                    # Central config — reads CloudFormation exports + env vars (lazy, cached)
├── requirements.txt
├── .env.example                 # Template — copy to .env and fill in your values
├── .gitignore
│
├── src/
│   ├── agent_orchestrator.py   # All 5 agents + WorkflowState + deploy pipeline
│   ├── agent_utils.py          # Terminal trace UI utilities (colour, AgentTrace)
│   ├── agent_observability.py  # X-Ray tracing + CloudWatch logging layer
│   ├── bedrock_kb_retrieval.py # Knowledge Base retrieval helper
│   ├── agentcore_cli.py        # AgentCore CLI wrapper (stage + deploy)
│   └── demo.py                 # Demo script (3 hardcoded end-to-end scenarios)
│
├── agentcore/
│   ├── agentcore.json           # AgentCore CLI runtime definition
│   ├── aws-targets.json         # Deployment target (written by CLI on first deploy)
│   └── cdk/                     # CDK app managed by the CLI
│
├── infrastructure/
│   ├── starter_stack.yaml       # CloudFormation: DynamoDB, S3, S3 Vectors, IAM, CloudWatch
│   ├── seed_data.py             # Seeds DynamoDB tables and S3 policy documents
│   └── cleanup.py               # Deletes all project resources
│
├── tests/
│   └── test_agent.py            # Full automated test suite (120 points)
│
└── docs/
    ├── architecture-overview.png
    ├── agents-and-tools-reference.png
    ├── request-flow-scenarios.png
    └── test-evidence/
        ├── 01-tests-120-of-120.png         # Full test suite passing
        ├── 02-xray-service-map-full.png    # X-Ray service map — full graph
        ├── 03-xray-service-map-top.png     # X-Ray service map — top detail
        ├── 04-xray-service-map-bottom.png  # X-Ray service map — bottom detail
        ├── 05-status-inventory-refund.png  # Order status + refund routing
        └── 06-orchestrator-calculation.png # Direct calculation scenario
```

---

## Setup

**Prerequisites**
- Python 3.12
- AWS account with Bedrock and AgentCore access enabled (`us-east-1`)
- Node.js 20+ (for the AgentCore CLI)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) Python package manager

**1 — Install dependencies**
```bash
pip install -r requirements.txt
npm install -g @aws/agentcore@0.30.0
```

**2 — Deploy infrastructure**
```bash
aws cloudformation deploy \
  --template-file infrastructure/starter_stack.yaml \
  --stack-name udacity-agentcore \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

python infrastructure/seed_data.py
```

**3 — Configure environment**
```bash
cp .env.example .env
# Fill in RETURNS_KB_ID, SHIPPING_KB_ID, WARRANTY_KB_ID after creating KBs in AWS Console
python config.py   # verify all resources resolved
```

**4 — Deploy to AgentCore Runtime**
```bash
python src/agent_orchestrator.py deploy
# Prints Runtime ARN, Guardrail ID/Version — copy into .env
```

**5 — Run locally**
```bash
python src/agent_orchestrator.py test    # 3 end-to-end scenarios, traced to X-Ray
python src/agent_orchestrator.py chat    # interactive terminal session
```

**6 — Invoke deployed runtime**
```bash
python src/agent_orchestrator.py invoke "What is the return policy for premium customers?" CUST-002
agentcore invoke '{"prompt": "I want to return my order ORD-27176", "customer_id": "CUST-001"}'
```

**7 — Cleanup**
```bash
python infrastructure/cleanup.py --yes
```

---

## Test results

```
python tests/test_agent.py all
```

**120 / 120 — all tests passing.** See `docs/test-evidence/01-tests-120-of-120.png`.

| Scenario | Routing | Result |
|---|---|---|
| `"I want to return my order ORD-27176"` (CUST-001) | Orchestrator → Inventory → Refund → Communication | ✅ Return approved, reference issued |
| `"What is the return policy for premium customers?"` | Orchestrator → Policy (3 parallel KBs) → Communication | ✅ Grounded policy answer |
| `"How much are 5 items at $29.99 with 10% off?"` | Orchestrator → Communication (direct) | ✅ Correct: $134.96 |

X-Ray service map evidence in `docs/test-evidence/02–04`.

---

## Key engineering decisions

**Orchestrator never writes the final response**
The OrchestratorAgent is only permitted to route. Every response — even a simple calculation — goes through CommunicationAgent. This enforces a clean separation: routing logic and response composition never mix.

**Shared WorkflowState with optimistic locking**
All agents read and write to a single DynamoDB record per session. Optimistic locking (version-based conditional writes) prevents concurrent updates from silently overwriting each other. Workers read the accumulated state left by previous agents, so context builds up naturally across the pipeline.

**Parallel multi-agent RAG**
PolicyAgent fans out to three retriever sub-agents simultaneously using `ThreadPoolExecutor`. All three Knowledge Bases are queried at once and results merged. This halves latency compared to sequential retrieval while keeping each retriever focused on its own domain.

**Guardrails applied per model call**
Bedrock Guardrails are enforced on every `BedrockModel` invocation — not at the gateway level. This means the safety layer is active whether the system runs locally or on the deployed runtime, and cannot be bypassed by routing around the entry point.

**Config resolves lazily from CloudFormation**
`config.py` makes no AWS calls on import. Values are resolved on first access and cached. This keeps unit tests, linters, and `python config.py` working without live credentials, and gives a clear error message for each failure mode (no credentials / stack not deployed / export missing).

---

## Security

- `.env` is gitignored — never committed
- `.env.example` contains only empty placeholders
- Configuration values (KB IDs, runtime ARNs, guardrail IDs) are loaded from environment variables at runtime via `config.py`
- PII redaction (emails, phones anonymised; credit cards and SSNs blocked) enforced via Bedrock Guardrails

---

## License

Udacity Project License
