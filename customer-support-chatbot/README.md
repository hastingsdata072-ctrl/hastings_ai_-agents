# Customer Support Chatbot
### Built with Amazon Bedrock AgentCore · Amazon Nova Pro · AWS Lambda · DynamoDB

A prompt-engineered customer support chatbot that handles real support scenarios end-to-end — filing bug tickets, answering product and policy questions from a knowledge base, and routing out-of-scope requests to human agents. All routing, information-gathering, and grounding logic lives in a single system prompt with no hardcoded classifiers.

---

## What it does

The chatbot classifies every incoming message into one of three routes and handles it fully:

| Route | Behaviour |
|---|---|
| Bug report | Collects bug description, reproduction steps, and environment one question at a time, then files a ticket via `create_bug_report` and returns the ticket ID |
| Platform question | Answers from the shop FAQ (orders, shipping, returns, refunds, payments) — never invents policies |
| Anything else | Politely hands the customer off to the human support line |

---

## Architecture

```
Customer message
      │
      ▼
AgentCore Harness  ←  system_prompt.txt (routing + FAQ grounding)
      │
      └── create_bug_report tool
              │
              ▼
        AgentCore Gateway → AWS Lambda → DynamoDB (ticket store)
```

See [architecture.md](./architecture.md) for full service roles and request flow.

---

## AWS services used

| Service | Purpose |
|---|---|
| Amazon Bedrock AgentCore | Managed harness — agent loop, session memory, tool execution |
| Amazon Nova Pro (`us.amazon.nova-pro-v1:0`) | Foundation model — all routing, collection, and responses |
| AgentCore Gateway | Exposes the bug report Lambda as a callable tool |
| AWS Lambda | Bug report tool runtime |
| Amazon DynamoDB | Ticket store — persists every filed bug report |
| Amazon Bedrock Evaluations | LLM-as-a-judge scoring of agent responses |
| AWS CloudFormation | Infrastructure provisioning |

---

## Repository layout

```
customer-support-chatbot/
├── README.md
├── architecture.md
│
├── src/                          # Runnable scripts
│   ├── main.py                   # Agent harness with full tool + error handling
│   ├── chat.py                   # Terminal chat client (multi-turn sessions)
│   ├── create_harness.py         # Creates / updates the AgentCore harness
│   ├── setup_gateway.py          # Registers the Lambda as an AgentCore tool
│   ├── generate-eval-dataset.py  # Runs test suite → JSONL for Bedrock Evaluations
│   └── cleanup_agentcore.py      # Tears down all AgentCore resources
│
├── lambda/
│   └── create_bug_report.py      # Lambda — validates inputs and writes to DynamoDB
│
├── infra/
│   ├── cloudformation-tool.yaml      # DynamoDB + Lambda + IAM roles stack
│   ├── cloudformation-testing.yaml   # S3 + evaluation role stack
│   └── eval-job-correctness.sh       # Evaluation job script
│
├── config/
│   └── system_prompt.txt         # The chatbot's system prompt (phone number scrubbed)
│
├── data/
│   ├── online_shop_faq.md        # Shop FAQ embedded in the system prompt at deploy time
│   ├── harness-tests.json        # Test suite covering all three routing scenarios
│   └── harness-tests-template.json
│
└── docs/
    ├── reflection.md             # Design decisions and production considerations
    └── test-evidence/            # Screenshots from all test scenarios
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

**2 — Add your resource IDs to main.py**

Open `src/main.py` and fill in your actual values:
```python
GATEWAY_URL = "https://<your-gateway-alias>.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
KB_ID       = "<your-knowledge-base-id>"
REGION      = "us-east-1"
MEMORY_ID   = "<your-memory-id>"
```
Do not commit these values. Add `agentcore_config.json` and `.env` to your `.gitignore`.

**3 — Deploy and chat**
```bash
python src/create_harness.py   # first run takes ~2–3 min
python src/chat.py             # start a fresh conversation
```

Iterate by editing `config/system_prompt.txt`, re-running `create_harness.py`, and starting a new `chat.py` session.

**4 — Run automated evaluation**
```bash
python src/generate-eval-dataset.py --tests-json data/harness-tests.json
# Upload output_eval_dataset.jsonl to S3 and run Bedrock Evaluations
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
| 01 | FAQ — covered question (e.g. return policy) | Answers from FAQ only | Correct answer, no fabrication |
| 02 | FAQ — uncovered question (e.g. gift wrapping) | Hands off to human support line | Correct handoff |
| 03 | Out of scope (e.g. weather question) | Politely redirects to support line | Correct handoff |
| 04 | Automated evaluation — correctness score | ≥ 0.90 | **0.94** |
| 05–07 | Evaluation details — per-case breakdown | All three routes covered | Pass |

---

## Key design decisions

**Prompt-based routing over a classifier**
All routing logic lives in `system_prompt.txt`. This makes the system fully transparent — changing behaviour means editing a text file, not redeploying code. It also makes failures obvious: if the agent routes incorrectly, the prompt is the first place to look.

**One question at a time for bug collection**
The AgentCore harness maintains session state across turns, so the agent can collect description, reproduction steps, and environment in sequence rather than asking for everything at once. Asking all three fields in one message produces worse completion rates — users skip fields they find inconvenient.

**FAQ embedded directly in the prompt**
The shop FAQ is short and stable, so embedding it directly at harness-creation time (via the `{{FAQ}}` placeholder) is the right call. For larger or frequently-updated documents, RAG with a Bedrock Knowledge Base would be the correct approach.

**Evaluation with LLM-as-a-judge**
Manual testing with `chat.py` is useful for debugging but not scalable. `generate-eval-dataset.py` runs every test case programmatically and produces a JSONL file for Bedrock Evaluations, giving a reproducible correctness score (0.94 on the final test suite).

---

## License

Udacity Project License
