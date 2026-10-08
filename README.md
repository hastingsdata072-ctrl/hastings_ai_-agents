# AI Agents — Amazon Bedrock Portfolio

Three production-style AI agent projects built on Amazon Bedrock AgentCore, AWS Lambda, and the Strands Agents framework. Each project is self-contained with its own README, architecture diagram, source code, infrastructure, and test evidence.

---

## Projects

### 1. [Customer Support Chatbot](./customer-support-chatbot/)
A prompt-engineered chatbot that handles customer support scenarios end-to-end — filing bug tickets, answering FAQ questions, and routing out-of-scope requests to human agents. All routing and grounding logic lives in a single system prompt.

**Stack:** Amazon Bedrock AgentCore · Amazon Nova Pro · AWS Lambda · DynamoDB · Bedrock Evaluations

---

### 2. [AI Support Agent](./ai-support-agent/)
A fully deployed AI support agent with order tracking, refund processing, loyalty discount calculation, live web browsing, and cross-session memory. Built with the Strands Agents framework on top of AgentCore.

**Stack:** Amazon Bedrock AgentCore · Strands Agents · Amazon Nova 2 Lite · AWS Lambda · Bedrock Knowledge Base · AgentCore Memory · Code Interpreter · AgentCore Browser

---

### 3. [NovaMart Multi-Agent Support System](./novamart-multi-agent-support/)
A production-grade multi-agent system that routes customer requests through a 5-agent hierarchy — inventory lookup, parallel multi-agent RAG across 3 knowledge bases, refund eligibility decisions, and response composition. Fully deployed on AgentCore Runtime with Bedrock Guardrails, AgentCore Memory, and end-to-end X-Ray observability. **120/120 on the automated test suite.**

**Stack:** Strands Agents · Amazon Bedrock AgentCore · Claude Haiku 4.5 + Sonnet 4.5 · DynamoDB · Bedrock Knowledge Bases × 3 · Bedrock Guardrails · AgentCore Memory · AWS X-Ray · CloudWatch

---

## AWS services used across all projects

| Service | Used in |
|---|---|
| Amazon Bedrock AgentCore (managed harness / runtime) | All three |
| Amazon Nova Pro / Nova 2 Lite | Chatbot, AI Support Agent |
| Claude Haiku 4.5 / Sonnet 4.5 | NovaMart |
| AgentCore Gateway (MCP) | Chatbot, AI Support Agent |
| AWS Lambda | Chatbot, AI Support Agent |
| Amazon DynamoDB | Chatbot, NovaMart |
| Amazon Bedrock Knowledge Base | AI Support Agent, NovaMart |
| AgentCore Memory | AI Support Agent, NovaMart |
| AgentCore Code Interpreter | AI Support Agent |
| AgentCore Browser | AI Support Agent |
| Amazon Bedrock Guardrails | NovaMart |
| AWS X-Ray | NovaMart |
| Amazon CloudWatch Logs | NovaMart |
| Amazon Bedrock Evaluations | Chatbot |
| AWS CloudFormation | All three |

---

## Security note

AWS credentials, API keys, and sensitive resource identifiers are kept out of source control. Each project includes a `.gitignore` that excludes `.env` files and generated artifacts. Configuration values are loaded from environment variables at runtime. See each project's `.env.example` for the required keys.
