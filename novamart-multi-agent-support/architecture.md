# Architecture — NovaMart Multi-Agent Support System

## System overview

```
Customer message (CLI / AgentCore Runtime invoke)
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock AgentCore Runtime               │
│                    (managed ASGI, arm64, Python 3.12)             │
│                                                                   │
│  agent_orchestrator.py  →  serve mode (HTTP entrypoint)          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    OrchestratorAgent                        │  │
│  │              Claude Haiku 4.5 | temperature 0.0            │  │
│  │         Creates WorkflowState → routes → never responds     │  │
│  │                                                             │  │
│  │  Tools                                                      │  │
│  │  ├── initialize_session       → creates WorkflowState row   │  │
│  │  ├── route_to_inventory_agent → calls InventoryAgent        │  │
│  │  ├── route_to_policy_agent    → calls PolicyAgent           │  │
│  │  ├── route_to_refund_agent    → calls RefundAgent           │  │
│  │  └── route_to_communication_agent → calls CommunicationAgent│  │
│  └─────────────────────────────────────────────────────────────┘  │
│           │              │               │              │          │
│           ▼              ▼               ▼              ▼          │
│  InventoryAgent    PolicyAgent      RefundAgent  CommunicationAgent│
│  Sonnet 4.5        Sonnet 4.5       Sonnet 4.5   Sonnet 4.5       │
│  temp 0.1          temp 0.2         temp 0.1     temp 0.3         │
│  DynamoDB reads    3 parallel KBs   DynamoDB     reads full       │
│                    (fan-out)        write         WorkflowState    │
│                         │                                         │
│              ┌──────────┼──────────┐                              │
│              ▼          ▼          ▼                              │
│   ReturnsPolicyRetriever ShippingPolicyRetriever WarrantyRetriever │
│   (Bedrock KB)           (Bedrock KB)            (Bedrock KB)     │
│              └── all run in parallel (ThreadPoolExecutor) ────────┘│
└───────────────────────────────────────────────────────────────────┘
        │
        ▼ (every request)
  WorkflowStateTable (DynamoDB) — shared agent context, optimistic locking
  X-Ray trace + CloudWatch log
  Bedrock Guardrail (per model call)
```

---

## Request flows

### Flow 1 — Order status / return / refund
```
Customer: "I want to return my order ORD-27176"

Orchestrator
  → initialize_session         (creates WorkflowState)
  → route_to_inventory_agent   (InventoryAgent reads DynamoDB: order age, tier)
  → route_to_refund_agent      (RefundAgent: 60-day Premium window → APPROVED, writes RET-xxx to DynamoDB)
  → route_to_communication_agent (CommunicationAgent reads full WorkflowState, writes final reply)

Response: "Your return has been approved. Reference: RET-XXXXXXXX ..."
```

### Flow 2 — Policy question (parallel multi-agent RAG)
```
Customer: "What is the return policy for premium customers?"

Orchestrator
  → initialize_session
  → route_to_policy_agent
        PolicyAgent calls search_all_policies(query)
          ├── ReturnsPolicyRetrieverAgent  → Bedrock KB (returns)   ┐
          ├── ShippingPolicyRetrieverAgent → Bedrock KB (shipping)  ├── parallel
          └── WarrantyPolicyRetrieverAgent → Bedrock KB (warranty)  ┘
        PolicyAgent synthesizes merged results
  → route_to_communication_agent

Response: Grounded policy answer, no invented facts
```

### Flow 3 — Calculation (direct path)
```
Customer: "How much are 5 items at $29.99 with 10% off?"

Orchestrator
  → initialize_session
  → calculates: 5 × $29.99 = $149.95 − 10% = $134.96
  → route_to_communication_agent  (presents result with working shown)

Response: "$134.96 — here's how: ..."
```

---

## Service roles

| Service | Role |
|---|---|
| **Amazon Bedrock AgentCore Runtime** | Managed deployment target — packages the agent, handles ASGI serving, scaling, and `agentcore invoke` |
| **Claude Haiku 4.5** | Orchestrator model — fast, cost-efficient routing decisions |
| **Claude Sonnet 4.5** | Worker model — more capable reasoning for data retrieval, policy synthesis, eligibility decisions, and response composition |
| **Amazon DynamoDB** | Three tables: Orders, Customers, WorkflowState. WorkflowState carries accumulated agent context for the session with optimistic locking (version counter + conditional writes) |
| **Amazon Bedrock Knowledge Bases × 3** | Returns, Shipping, Warranty policies. Backed by S3 Vectors (vector bucket + one index per KB, `amazon.titan-embed-text-v2:0` embeddings) |
| **Amazon Bedrock Guardrails** | Applied per `BedrockModel` call: content filtering (SEXUAL, VIOLENCE, HATE at HIGH; INSULTS, MISCONDUCT at MEDIUM), PII redaction, topic blocking (competitor products, pricing negotiations, legal threats), profanity filtering |
| **AgentCore Memory** | SESSION_SUMMARY strategy, 7-day retention — preserves context across turns so customers don't repeat themselves |
| **AWS X-Ray** | End-to-end trace per request: Orchestrator → Worker → Knowledge Base call chain. 100% sampling in dev. Published via `xray:PutTraceSegments` from both local and deployed runtime |
| **Amazon CloudWatch Logs** | INFO-level structured logs to `/aws/bedrock/agentcore/udacity-agentcore`. CloudWatch Transaction Search enabled |
| **AWS CloudFormation** | Provisions DynamoDB tables, S3 policy-docs bucket, S3 Vectors bucket + 3 indexes, AgentCore execution role, CloudWatch log group |
| **AgentCore CLI (`@aws/agentcore`)** | Packages `build/runtime/` with arm64-compatible wheels and deploys via a CDK stack (`AgentCore-udacity-default`) |

---

## WorkflowState design

Every session creates one DynamoDB row (`WorkflowStateTable`). Agents read and write it as they run:

```
WorkflowState row
├── session_id      (partition key)
├── customer_id
├── created_at
├── version         (optimistic lock counter — increments on every write)
├── ttl             (auto-expiry after 24 h)
├── inventory_agent (written by InventoryAgent after it runs)
├── policy_agent    (written by PolicyAgent after it runs)
├── refund_agent    (written by RefundAgent after it runs)
└── communication_agent (written by CommunicationAgent)
```

Write pattern — conditional update:
```python
table.update_item(
    Key={'session_id': session_id},
    UpdateExpression="SET inventory_agent = :data, version = :new_version",
    ConditionExpression="version = :expected_version",
    ...
)
```
If two agents write simultaneously and versions collide, the update retries with a fresh read (up to 3 attempts). This prevents silent data loss in concurrent scenarios.

---

## Multi-agent RAG — parallel fan-out

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(returns_retriever,  query),
        executor.submit(shipping_retriever, query),
        executor.submit(warranty_retriever, query),
    ]
    for future in as_completed(futures):
        domain, text = future.result()
        results[domain] = text
```

All three Knowledge Bases are queried simultaneously. Results arrive in completion order and are assembled into a stable `Returns / Shipping / Warranty` output before being handed to PolicyAgent for synthesis. One failing retriever does not block the others.

---

## Observability pipeline

```
Request arrives
    │
    ├── X-Ray segment opened (trace_id logged)
    │       └── each route_to_* tool → X-Ray subsegment (worker node on service map)
    │               └── each KB retrieval → X-Ray subsegment (KnowledgeBase node)
    │
    ├── CloudWatch: structured INFO log per agent call
    │
    └── X-Ray segment closed, published via xray:PutTraceSegments
```

Works identically from local (`test`, `chat`) and from the deployed runtime (`invoke`). The X-Ray service map shows the full Orchestrator → Worker → Knowledge Base call chain.

---

## Guardrail application

Guardrails are applied at the `BedrockModel` level, not at the gateway:

```python
model = BedrockModel(
    model_id=config.WORKER_MODEL_ID,
    guardrail_id=config.GUARDRAIL_ID,
    guardrail_version=config.GUARDRAIL_VERSION,
    ...
)
```

This means the safety layer is active for every agent call — locally and in the deployed runtime — regardless of how the system is invoked. It cannot be bypassed by routing around the entry point.

---

## Deployment pipeline

`python src/agent_orchestrator.py deploy` runs six steps:

| Step | Action |
|---|---|
| 1/6 | Build all 5 agents locally and validate the graph |
| 2/6 | Create Bedrock Guardrail + versioned policy |
| 3/6 | Stage code in `build/runtime/`, write runtime settings to `agentcore/agentcore.json`, deploy with `agentcore deploy -y` |
| 4/6 | Create AgentCore Memory (SESSION_SUMMARY, 7-day retention) |
| 5/6 | Configure observability (CloudWatch + X-Ray Transaction Search); second `agentcore deploy -y` to apply env vars |
| 6/6 | Deploy AgentCore Gateway (skipped if Lambda tool functions not deployed) |
