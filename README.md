# AI Agents — Amazon Bedrock Portfolio

Two production-style AI agent projects built on Amazon Bedrock AgentCore, AWS Lambda, and the Strands Agents framework. Each project is self-contained with its own README, architecture diagram, source code, infrastructure, and test evidence.

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

## AWS services used across both projects

| Service | Used in |
|---|---|
| Amazon Bedrock AgentCore (managed harness) | Both |
| Amazon Nova Pro / Nova 2 Lite | Both |
| AgentCore Gateway (MCP) | Both |
| AWS Lambda | Both |
| Amazon DynamoDB | Chatbot |
| Amazon Bedrock Knowledge Base | AI Support Agent |
| AgentCore Memory | AI Support Agent |
| AgentCore Code Interpreter | AI Support Agent |
| AgentCore Browser | AI Support Agent |
| Amazon Bedrock Evaluations | Chatbot |
| AWS CloudFormation | Both |

---

## Security note

No API keys, AWS credentials, resource ARNs, or environment-specific secrets are committed to this repository. All sensitive values are referenced by placeholder and must be supplied locally. See each project's `.gitignore` for exclusion rules.
