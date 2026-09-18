# Architecture — Customer Support AI Agent

## System overview

```
Customer (CLI / agentcore invoke)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              BedrockAgentCoreApp (ASGI server)              │
│                      invoke() entrypoint                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Strands Agent                        │   │
│  │   Model: Amazon Nova 2 Lite (global cross-region)    │   │
│  │                                                      │   │
│  │  Tools                                               │   │
│  │  ├── search_knowledge_base     (Bedrock KB retrieve) │   │
│  │  ├── calculate_loyalty_discount (Code Interpreter)   │   │
│  │  ├── browser                   (AgentCore Browser)   │   │
│  │  └── Gateway tools (MCP over streamable HTTP)        │   │
│  │       ├── get_order            → order_tracker λ     │   │
│  │       ├── get_customer_orders  → order_tracker λ     │   │
│  │       ├── get_customer         → order_tracker λ     │   │
│  │       ├── initiate_refund      → refund_processor λ  │   │
│  │       ├── check_refund_status  → refund_processor λ  │   │
│  │       └── get_return_label     → refund_processor λ  │   │
│  │                                                      │   │
│  │  Hooks                                               │   │
│  │  └── MemoryHook                                      │   │
│  │       ├── retrieve_customer_context (MessageAdded)   │   │
│  │       └── save_support_interaction (AfterInvocation) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Service roles

| Service | Role in this system |
|---|---|
| **Amazon Bedrock AgentCore** | Managed ASGI runtime — hosts the agent, handles deployment, scaling, and the `agentcore invoke` interface |
| **Amazon Nova 2 Lite** | Foundation model — drives all reasoning, routing, and response generation |
| **AgentCore Gateway (MCP)** | Exposes Lambda functions as tools via the MCP protocol over streamable HTTP; the agent connects at runtime |
| **AWS Lambda — order_tracker** | Handles order and customer lookup via API Gateway proxy integration (GET routes) |
| **AWS Lambda — refund_processor** | Handles refund initiation, status checks, and return label generation; invoked directly by the Gateway |
| **Amazon Bedrock Knowledge Base** | Vector store for product catalogue, return policies, warranty info, and loyalty programme details; queried via `bedrock:Retrieve` |
| **AgentCore Code Interpreter** | Sandboxed Python execution environment used for deterministic loyalty discount arithmetic |
| **AgentCore Browser** | Managed browser session for live web lookups when the customer asks about real-time information |
| **AgentCore Memory** | Long-term customer memory — stores and retrieves facts and preferences across sessions using SEMANTIC and USER_PREFERENCE strategies |
| **Amazon CloudWatch** | Receives all tool-level error logs from `logger.error()` calls in the agent and Lambda functions |

---

## Request flow

1. Customer sends a message via `agentcore invoke`
2. `invoke()` creates a `MemoryHook` for the customer's `actor_id` and `session_id`
3. `MemoryHook.retrieve_customer_context` fires on the incoming message — retrieves relevant memories and prepends them to the prompt
4. The agent connects to the Gateway via MCP and loads the available tools
5. The Strands agent loop calls the model; the model selects a tool based on the request
6. The tool executes (Lambda, KB retrieval, Code Interpreter, or Browser) and returns a result
7. The model incorporates the result and produces a response
8. `MemoryHook.save_support_interaction` fires after invocation — saves the turn to long-term memory
9. The response text is returned to the caller

---

## Error handling strategy

All Gateway-related failures are caught in a nested `try/except` inside `invoke()`:

- `ConnectionError` / `TimeoutError` — returns a specific connectivity failure message
- Any other `Exception` inside the Gateway block — returns a general tool failure message
- Any `Exception` outside the Gateway block — returns a generic unexpected error message

No exception objects, tracebacks, or environment variables are ever included in user-facing responses. All real exceptions are logged server-side via `logger.error()`.
