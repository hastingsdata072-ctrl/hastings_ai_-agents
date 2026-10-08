# Reflection — NovaMart Multi-Agent Support System

## Design decision: orchestrator as a pure router

The most deliberate architectural choice in this project is that the OrchestratorAgent is never allowed to write the final customer-facing response. Even on a simple calculation — where the orchestrator already has a complete answer — it must delegate to CommunicationAgent as its last action. This constraint looks like overhead until you consider what it prevents: routing logic and response composition silently merging into a single agent with unclear responsibilities.

Enforcing the separation also made testing cleaner. Each agent's output is independently verifiable in WorkflowState before CommunicationAgent reads it. If a response is wrong, you can trace exactly which agent produced the bad output, rather than debugging a single monolithic agent that does everything.

---

## Design decision: parallel multi-agent RAG over sequential retrieval

PolicyAgent fans out to three retriever sub-agents simultaneously using `ThreadPoolExecutor`. The alternative — querying the three Knowledge Bases sequentially — would roughly triple the latency of every policy question. Since all three retrievers are independent (Returns, Shipping, Warranty have no dependency on each other), there is no correctness reason to serialize them.

The tradeoff: parallel execution complicates stdout handling. All three retriever threads write to the same terminal, which produces interleaved output. The solution was a trace suppression flag (`_suppress_parallel`) set before the fan-out and cleared after, with results printed sequentially once all futures complete. This keeps the terminal UI readable without sacrificing the latency benefit.

---

## Challenge: WorkflowState version conflicts under concurrency

WorkflowState uses optimistic locking — every write includes a version check via DynamoDB's `ConditionExpression`. During testing, rapid sequential agent calls occasionally produced `ConditionalCheckFailedException` when an agent tried to write before the previous write had propagated. The initial implementation had no retry logic and simply failed.

The fix was straightforward: wrap each `_update_workflow_state` call in a retry loop that reads the current version after a conflict and retries up to three times with a small back-off. This resolved all conflicts in testing without introducing pessimistic locks, which would have serialized the agent pipeline unnecessarily.

---

## Challenge: silent agent failures from missing IAM permissions

During development, the Knowledge Base retrievers and the AgentCore Browser silently failed — the agent apologised for a limitation and fabricated a plausible-sounding answer rather than raising an error. This is a genuinely dangerous failure mode in a customer-facing system: customers receive wrong information, and there is no visible signal that something went wrong.

Diagnosing this required checking CloudWatch logs and the execution role's effective permissions. The auto-created role had permissions for DynamoDB, model invocation, and X-Ray, but was missing `bedrock:Retrieve` on the Knowledge Base ARNs and the permission needed to start AgentCore Browser sessions. The fix was a scoped inline policy granting exactly those two capabilities. Both tools functioned correctly after the policy update.

The production lesson is the same one that appeared in the simpler projects: silent degradation is more costly than a visible error, because neither customers nor operators have any signal that something needs fixing. Any production deployment of this system should have explicit tool-level failure logging and a CloudWatch alarm on the tool error rate.

---

## Production consideration: 100% X-Ray sampling is a dev setting

The observability configuration sets `samplingRate=1.0` — every request is traced. This is appropriate during development and evaluation: full trace coverage makes it easy to verify the Orchestrator → Worker → Knowledge Base call chain and debug routing decisions.

In production, 1.0 sampling would generate significant CloudWatch costs at scale and add measurable latency to every request. The correct production value is typically 0.05 (5%) for steady-state traffic, with the ability to increase it temporarily for debugging. This is a one-line change in `configure_observability()`, but it is worth making deliberately before any production deployment rather than discovering the cost impact after the fact.
