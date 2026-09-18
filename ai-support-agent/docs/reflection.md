# Reflection — AI Support Agent

## Design decision: loyalty discount calculation

The `calculate_loyalty_discount` tool required deterministic rules for points redemption. The project brief specified capping redemption at 50% of the order value and flooring to the nearest 500 points, but left the points-to-dollar conversion rate open. I chose a 100-points-per-dollar ratio and applied it before the tier discount rather than after — so the tier percentage always applies to the customer's true out-of-pocket cost, not the full list price. This produces a more defensible number for the customer and avoids a subtle double-discount that would erode margins.

More importantly, I ran this arithmetic inside the AgentCore Code Interpreter rather than letting the model compute it inline. LLMs are unreliable at multi-step arithmetic involving rounding and floor operations — the kind of off-by-one that a real customer would notice and escalate immediately. Delegating numeric computation to a deterministic execution environment is the correct default for any calculation that appears in a customer-facing response.

---

## Challenge: silent tool failures

After initial deployment, two tools — the Knowledge Base search and the Browser tool — failed without raising an exception. The agent did not error out; instead it apologised for a "system limitation" and returned a plausible-sounding fabricated answer. In a customer support context, that failure mode is more dangerous than a visible error: customers and support staff have no signal that something went wrong, and the fabricated response may be acted on.

Diagnosing this required checking CloudWatch logs and the runtime's IAM role. The auto-created execution role had permissions for Memory, Code Interpreter, and model invocation, but nothing for `bedrock:Retrieve` on the Knowledge Base or for starting AgentCore Browser sessions. The fix was a scoped inline policy granting exactly those two capabilities against the specific KB and browser ARNs. Both tools functioned correctly after the policy was attached.

---

## Production consideration: observability over graceful degradation

The silent failure incident above shaped my strongest takeaway from this project. Graceful degradation — the agent apologising and continuing — feels like good UX, but it hides operational failures from everyone who needs to know about them. A permissions gap, a timeout, or a tool regression all produce the same polite response, with no observable difference to the customer or to monitoring systems.

In a production deployment I would add two controls that this project lacks:

1. **Explicit tool-level exception logging** — every tool call that fails raises a structured log event with the tool name, error type, and session ID, regardless of how the agent handles it in its response
2. **Alerting on tool failure rate** — a CloudWatch alarm on the tool error log stream, so a regression in any downstream integration surfaces within minutes rather than through customer complaints

The core principle: make failures loud to operators even when they are handled gracefully for users. Silent degradation at scale means bugs survive far longer than they should.
