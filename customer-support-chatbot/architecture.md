# Architecture — Customer Support Chatbot

## System overview

```
Customer message
      │
      ▼
┌─────────────────────────────────────────────────┐
│         Amazon Bedrock AgentCore Harness        │
│              (managed agent loop)               │
│                                                 │
│  system_prompt.txt                              │
│    ├── Routing logic   (3 categories)           │
│    ├── Bug collection  (3 required fields)      │
│    └── FAQ grounding   ({{FAQ}} placeholder)    │
│                                                 │
│  Model: Amazon Nova Pro                         │
│  (us.amazon.nova-pro-v1:0)                      │
│                                                 │
│  Tools                                          │
│  └── create_bug_report (via AgentCore Gateway)  │
│            │                                    │
│            ▼                                    │
│       AWS Lambda                                │
│       DynamoDB table (ticket store)             │
└─────────────────────────────────────────────────┘
```

---

## Request flow

1. Customer sends a message
2. AgentCore harness passes it to the model with `system_prompt.txt` injected
3. The model classifies the message into one of three categories:
   - **Bug report** — collects description, reproduction steps, and environment one field at a time across turns, then calls `create_bug_report`
   - **Platform question** — answers directly from the embedded FAQ; no tool call needed
   - **Anything else** — returns a polite handoff message with the human support line
4. If `create_bug_report` is called, the Gateway invokes the Lambda which writes a ticket to DynamoDB and returns a `ticketId`
5. The model relays the ticket ID to the customer

---

## Service roles

| Service | Role |
|---|---|
| **Amazon Bedrock AgentCore** | Managed harness — runs the agent loop, handles session memory, routes tool calls |
| **Amazon Nova Pro** | Foundation model driving all classification, collection, and response generation |
| **AgentCore Gateway** | Exposes the `create_bug_report` Lambda as a callable tool |
| **AWS Lambda** | Executes the bug report tool — validates inputs and writes to DynamoDB |
| **Amazon DynamoDB** | Persistent ticket store — each filed bug report is a table item with a unique `ticketId` |
| **Amazon Bedrock Evaluations** | LLM-as-a-judge evaluation — scores agent responses against expected outcomes |
| **AWS CloudFormation** | Provisions all infrastructure (DynamoDB, Lambda, IAM roles, S3 evaluation bucket) |

---

## Prompt-based routing

All routing, information-gathering, and grounding logic lives in `config/system_prompt.txt`. There are no condition nodes, classifiers, or hardcoded branching outside the prompt. This keeps the system transparent — every behaviour change is a prompt edit, and iteration requires only re-running `create_harness.py`.

The `{{FAQ}}` placeholder in the prompt is replaced at harness-creation time by `create_harness.py` with the full contents of `data/online_shop_faq.md`.

---

## Error handling

Gateway and tool failures are caught at the harness level. Sanitised messages are returned to the customer; real exceptions are logged server-side. No stack traces, ARNs, or environment variables are ever included in a user-facing response.
