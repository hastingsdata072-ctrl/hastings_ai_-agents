# Customer Support AI Agent
### Built with Amazon Bedrock AgentCore · Python · AWS Lambda · DynamoDB

A production-style AI chatbot that handles real customer support scenarios end-to-end — filing bug tickets, answering product questions from a knowledge base, and handing off out-of-scope requests to human agents. Built on Amazon Bedrock AgentCore's managed harness with a full automated evaluation pipeline.

---

## What it does

Customers interact with the chatbot in natural language. The agent classifies each message and responds appropriately across three routes:

| Scenario | Agent behaviour |
|---|---|
| Bug report | Collects description, reproduction steps, and environment over multiple turns, then files a ticket via the `create_bug_report` tool and returns a ticket ID |
| Platform question | Answers from the shop's FAQ using prompt-embedded retrieval |
| Out of scope | Politely routes the customer to the human support line |

Routing, information gathering, and grounding all live in a single, carefully engineered system prompt — no hardcoded classifiers or condition nodes.

---

## Architecture

```
Customer → AgentCore Managed Harness
               │
               ├─ system_prompt.txt  (routing + grounding logic)
               ├─ online_shop_faq.md (embedded knowledge base)
               │
               └─ AgentCore Gateway
                       │
                       └─ Lambda: create_bug_report → DynamoDB
```

**Key design choices:**
- **Session memory** is handled by AgentCore — the agent asks for missing bug report fields one at a time across turns without losing context
- **FAQ grounding** uses direct prompt embedding (appropriate for short, stable content)
- **Error handling** isolates Gateway failures with nested exception handling, returning sanitized messages to users while logging the real exception server-side — no stack traces or secrets ever reach the response

---

## Stack

| Layer | Technology |
|---|---|
| AI runtime | Amazon Bedrock AgentCore (managed harness) |
| Model | Amazon Nova Pro (`us.amazon.nova-pro-v1:0`) |
| Tool gateway | Amazon Bedrock AgentCore Gateway |
| Tool runtime | AWS Lambda (Python 3.9) |
| Storage | Amazon DynamoDB |
| Evaluation | Amazon Bedrock Evaluations (LLM-as-a-judge) |
| Infrastructure | AWS CloudFormation |
| Region | `us-east-1` |

---

## Repository layout

```
customer-support-agent/
├── src/                          # All runnable Python
│   ├── main.py                   # Agent entrypoint with Gateway error handling
│   ├── chat.py                   # Terminal chat client (multi-turn sessions)
│   ├── create_harness.py         # Creates / updates the managed harness
│   ├── create_bug_report.py      # Lambda function — stores tickets in DynamoDB
│   ├── setup_gateway.py          # Registers the Lambda as an AgentCore tool
│   ├── generate-eval-dataset.py  # Runs test suite → JSONL for Bedrock Evaluations
│   └── cleanup_agentcore.py      # Tears down all AgentCore resources
│
├── config/
│   ├── system_prompt.txt         # Main deliverable — the chatbot's system prompt
│   ├── cloudformation-tool.yaml  # DynamoDB + Lambda + IAM stack
│   ├── cloudformation-testing.yaml # S3 + evaluation role stack
│   └── eval-job-correctness.sh   # Evaluation job script
│
├── data/
│   ├── online_shop_faq.md        # Embedded knowledge base
│   ├── harness-tests.json        # Test suite (FAQ, bug report, out-of-scope cases)
│   └── harness-tests-template.json
│
├── screenshots/                  # Test evidence and reviewer fix captures
├── COVER_NOTE.md                 # Submission cover note with testing evidence
├── reflection.md                 # Design decisions and production considerations
└── requirements.txt
```

---

## Running it locally

**Prerequisites**
- AWS account with Amazon Bedrock and AgentCore access enabled
- AWS CLI configured (`us-east-1`)
- Python 3.9+ with `pip install -r requirements.txt`
- Access to `us.amazon.nova-pro-v1:0`

**Deploy infrastructure**
```bash
# 1. Create DynamoDB table, Lambda, and IAM roles
aws cloudformation deploy \
  --template-file config/cloudformation-tool.yaml \
  --stack-name bug-report-tool-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# 2. Register the Lambda as an AgentCore tool
python src/setup_gateway.py
```

**Build and chat**
```bash
python src/create_harness.py   # ~2–3 min on first run
python src/chat.py             # Start a fresh session
```

Edit `config/system_prompt.txt`, re-run `create_harness.py`, and start a new `chat.py` session to iterate.

**Run automated evaluation**
```bash
python src/generate-eval-dataset.py --tests-json data/harness-tests.json
# Upload output_eval_dataset.jsonl to S3, then run Bedrock Evaluations
```

**Cleanup**
```bash
python src/cleanup_agentcore.py
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1
```

---

## Testing approach

Test coverage spans all three routing scenarios:

- **FAQ questions** — order tracking, refund processing, shipping queries
- **Bug reports** — multi-turn collection of all three required fields before tool invocation
- **Out-of-scope** — confirms handoff to human support without hallucinated answers

Evaluation uses Amazon Bedrock Evaluations (LLM-as-a-judge) on a JSONL dataset generated programmatically, giving a reproducible quality signal without manual review of every response.

---

## Key engineering decisions

**Why prompt-based routing instead of a classifier?** Keeping all logic in the system prompt makes iteration fast — no redeployment, just edit and re-run `create_harness.py`. It also keeps the routing transparent and auditable.

**Why one question at a time for bug collection?** AgentCore maintains session state, so the agent can ask for description, steps, and environment in sequence. Asking for all three at once produces worse completion rates — users skip fields they find inconvenient.

**Silent failure is a production risk.** During development, two tools failed quietly: the agent apologised for a "system limitation" and returned a plausible-sounding fabricated answer. The root cause was missing IAM permissions. The fix was a scoped inline policy — but the real lesson is that any production deployment of this system needs explicit tool-level failure logging and alerting, not graceful degradation that hides errors from operators.

---

## License

MIT
