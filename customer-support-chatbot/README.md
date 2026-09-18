# Customer Support Chatbot
### Built with Amazon Bedrock AgentCore · Amazon Nova Pro · AWS Lambda · DynamoDB

A prompt-engineered customer support chatbot that handles real support scenarios end-to-end — filing bug tickets, answering product and policy questions from a knowledge base, and routing out-of-scope requests to human agents. All routing, information-gathering, and grounding logic lives in a single system prompt with no hardcoded classifiers or condition nodes.

---

## What it does

The chatbot classifies every incoming message into one of three routes and handles it fully:

| Route | Behaviour |
|---|---|
| Bug report | Collects bug description, reproduction steps, and environment one question at a time across turns, then files a ticket via `create_bug_report` and returns the ticket ID |
| Platform question | Answers from the shop FAQ (orders, shipping, returns, refunds, payments) — never invents policies |
| Anything else | Politely hands the customer off to the human support line |

Routing, information gathering, and grounding all live in a single, carefully engineered system prompt — no hardcoded classifiers or condition nodes.

---

## Architecture

```
Customer message
      │
      ▼
AgentCore Managed Harness  ←  system_prompt.txt (routing + FAQ grounding)
      │
      ├─ online_shop_faq.md  (embedded at deploy time via {{FAQ}} placeholder)
      │
      └── create_bug_report tool
              │
              ▼
        AgentCore Gateway → AWS Lambda → DynamoDB (ticket store)
```

See [architecture.md](./architecture.md) for full service roles and request flow.

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
customer-support-chatbot/
├── README.md
├── architecture.md
│
├── src/                              # Runnable scripts
│   ├── chat.py                       # Terminal chat client (multi-turn sessions)
│   ├── create_harness.py             # Creates / updates the AgentCore harness
│   ├── setup_gateway.py              # Registers the Lambda as an AgentCore tool
│   ├── generate-eval-dataset.py      # Runs test suite → JSONL for Bedrock Evaluations
│   └── cleanup_agentcore.py          # Tears down all AgentCore resources
│
├── lambda/
│   └── create_bug_report.py          # Lambda — validates inputs, writes to DynamoDB
│
├── infra/
│   ├── cloudformation-tool.yaml      # DynamoDB + Lambda + IAM roles stack
│   ├── cloudformation-testing.yaml   # S3 + evaluation role stack
│   └── eval-job-correctness.sh       # Evaluation job script
│
├── config/
│   └── system_prompt.txt             # Chatbot system prompt (credentials scrubbed)
│
├── data/
│   ├── online_shop_faq.md            # Shop FAQ — embedded in prompt at deploy time
│   ├── harness-tests.json            # Test suite covering all three routing scenarios
│   └── harness-tests-template.json
│
└── docs/
    └── test-evidence/                # Screenshots from all test scenarios
        ├── 01-faq-covered-question.png
        ├── 02-faq-uncovered-handoff.png
        ├── 03-out-of-scope-handoff.png
        ├── 04-eval-correctness-score.png
        ├── 05-eval-details-page1.png
        ├── 06-eval-details-page1-full.png
        └── 07-eval-details-page2.png
```

---

## Setup and running

**Prerequisites**
- AWS account with Bedrock and AgentCore access enabled
- AWS CLI configured (`us-east-1`)
- Python 3.9+ with `pip install -r requirements.txt`
- Access to `us.amazon.nova-pro-v1:0`

**1 — Deploy infrastructure**
```bash
# DynamoDB table + Lambda + IAM roles
aws cloudformation deploy \
  --template-file infra/cloudformation-tool.yaml \
  --stack-name bug-report-tool-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Register the Lambda as an AgentCore tool
python src/setup_gateway.py
```

**2 — Configure resource IDs**

Open `src/create_harness.py` and `src/chat.py` and fill in your values — do not commit them:
```python
GATEWAY_URL = "https://<your-gateway-alias>.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
REGION      = "us-east-1"
```

**3 — Deploy and chat**
```bash
python src/create_harness.py   # first run takes ~2–3 min
python src/chat.py             # start a fresh conversation
```

Iterate by editing `config/system_prompt.txt`, re-running `create_harness.py`, and starting a new `chat.py` session.

**4 — Run automated evaluation**
```bash
python src/generate-eval-dataset.py --tests-json data/harness-tests.json
# Upload output_eval_dataset.jsonl to S3, then run Bedrock Evaluations
```

**5 — Cleanup**
```bash
python src/cleanup_agentcore.py
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1
```

---

## Test scenarios and results

| # | Scenario | Expected behaviour | Result |
|---|---|---|---|
| 01 | FAQ — covered question (return policy) | Answers from FAQ only, no fabrication | ✅ Pass |
| 02 | FAQ — uncovered question (gift wrapping) | Hands off to human support line | ✅ Pass |
| 03 | Out of scope (weather question) | Politely redirects to support line | ✅ Pass |
| 04 | Automated evaluation — correctness score | ≥ 0.90 | ✅ **0.94** |
| 05–07 | Evaluation details — per-case breakdown | All three routes covered | ✅ Pass |

---

## Key engineering decisions

**Prompt-based routing over a classifier**
All routing logic lives in `config/system_prompt.txt`. Changing behaviour means editing a text file, not redeploying code. Failures are transparent — if the agent routes incorrectly, the prompt is the first place to look.

**One question at a time for bug collection**
The AgentCore harness maintains session state across turns, so the agent collects description, reproduction steps, and environment in sequence. Asking for all three at once produces worse completion rates — users skip fields they find inconvenient.

**FAQ embedded directly in the prompt**
The shop FAQ is short and stable, so embedding it at harness-creation time via the `{{FAQ}}` placeholder is the right call. For larger or frequently-updated documents, RAG with a Bedrock Knowledge Base would be the correct approach.

**Evaluation with LLM-as-a-judge**
Manual testing with `chat.py` is useful for debugging but not scalable. `generate-eval-dataset.py` runs every test case programmatically and produces a JSONL file for Bedrock Evaluations, giving a reproducible correctness score (0.94 on the final suite).

**Error handling without exposing internals**
Gateway and tool failures are isolated in a nested `try/except`. All three failure branches return hardcoded, sanitised strings — no stack traces, ARNs, or environment variables ever reach the user-facing response. Real exceptions are logged server-side via `logger.error()`.

---

## License

Udacity Project License
