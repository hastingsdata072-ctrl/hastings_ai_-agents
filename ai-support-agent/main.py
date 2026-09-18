"""
Customer Support AI Agent — Starter Code
==========================================
Your task is to complete this file by implementing all sections marked
with # TODO comments.

Reference the step-by-step solution files and INSTRUCTIONS.md for guidance.
Do NOT copy the solution directly — work through each section yourself.

Run locally (after filling in config values):
  uv run main.py '{"prompt": "Hello", "customer_id": "CUST-123", "session_id": "s1"}'

Deploy to AgentCore:
  agentcore deploy

Invoke deployed agent:
  agentcore invoke '{"prompt": "Hello", "customer_id": "CUST-123", "session_id": "s1"}'
"""

# ── Imports ───────────────────────────────────────────────────────────────────
# These imports are provided. Do not remove them.
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
import argparse, json
import os, asyncio, boto3
from strands.hooks import (
    HookProvider, AfterInvocationEvent, HookRegistry, MessageAddedEvent,
)
import logging
import uuid
from typing import Dict
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands_tools.browser import AgentCoreBrowser


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("CSAI_Agent")

# ── TODO 1 — App Initialisation ───────────────────────────────────────────────
# Create a BedrockAgentCoreApp instance.
# This registers the ASGI server for AgentCore deployment.
# There must be exactly one instance per deployment.
#
# Hint: app = BedrockAgentCoreApp()

app = BedrockAgentCoreApp()


# Suppress interactive tool-consent prompts (required in headless deployments).
os.environ["BYPASS_TOOL_CONSENT"] = "true"


# ── TODO 2 — Configuration ────────────────────────────────────────────────────
# Replace the placeholder strings with your actual AWS resource values.
# You collected these in Part 1 of the INSTRUCTIONS.
#
# GATEWAY_URL format: https://<alias>.gateway.bedrock-agentcore.<region>.amazonaws.com/mcp
# KB_ID       format: 10-character alphanumeric string from the KB console
# REGION:     your AWS region, e.g. "us-east-1"
# MEMORY_ID   format: shown in the AgentCore Memory console

GATEWAY_URL = "https://customersupportgateway-6w60pzbixd.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
KB_ID       = "JCY1LKKIHE"
REGION      = "us-east-1"
MEMORY_ID   = "CustomerSupportMemory-MAEQP2CPLA"


# ── TODO 3 — Model and Clients ────────────────────────────────────────────────
# Create:
#   1. A BedrockModel using model_id "global.amazon.nova-2-lite-v1:0"
#   2. A MemoryClient with region_name=REGION
#   3. A boto3 client for the "bedrock-agent-runtime" service in REGION
#
# Hint: model = BedrockModel(model_id=model_id)

model_id = "global.amazon.nova-2-lite-v1:0"

model = BedrockModel(model_id=model_id)

memory_client = MemoryClient(region_name=REGION)

_bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)


# ── TODO 4 — Namespace Helper ─────────────────────────────────────────────────
# Implement get_namespaces() to return a dict mapping strategy type to
# namespace template string.
#
# Steps:
#   1. Call mem_client.get_memory_strategies(memory_id) to get strategy list
#   2. Return a dict: { strategy["type"]: strategy["namespaces"][0] for each strategy }
#
# Example output:
#   { "SEMANTIC": "cs_agent/{actorId}/facts",
#     "USER_PREFERENCE": "cs_agent/{actorId}/preferences" }

def get_namespaces(mem_client: MemoryClient, memory_id: str) -> Dict:
    """Return a dict mapping strategy type → namespace template string."""
    strategies = mem_client.get_memory_strategies(memory_id)
    return {s["type"]: s["namespaces"][0] for s in strategies}


# ── TODO 5 — Memory Hook ──────────────────────────────────────────────────────
# Implement MemoryHook, a HookProvider subclass that adds long-term memory.
#
# The class needs:
#   __init__(self, actor_id, session_id, memory_client, memory_id)
#     — store all four as instance attributes
#     — call get_namespaces() and store the result as self.namespaces
#
#   retrieve_customer_context(self, event: MessageAddedEvent)
#     — only runs for plain-text user messages (not tool results)
#     — for each strategy namespace, call memory_client.retrieve_memories(
#          memory_id, namespace (formatted with actorId), query, top_k=5)
#     — collect non-empty memory texts tagged with their strategy type
#     — if any memories found, prepend them to the user message as:
#          "Customer Context:\n<memories>\n\n<original_message>"
#
#   save_support_interaction(self, event: AfterInvocationEvent)
#     — walk the message list backwards to find the last plain-text user
#       query and the last assistant response
#     — call memory_client.create_event(memory_id, actor_id, session_id,
#          messages=[(customer_query, "USER"), (agent_response, "ASSISTANT")])
#
#   register_hooks(self, registry: HookRegistry)
#     — register retrieve_customer_context on MessageAddedEvent
#     — register save_support_interaction on AfterInvocationEvent

class MemoryHook(HookProvider):
    """Long-term memory hook for the customer support agent."""

    def __init__(
        self,
        actor_id: str,
        session_id: str,
        memory_client: MemoryClient,
        memory_id: str,
    ):
        self.actor_id = actor_id
        self.session_id = session_id
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.namespaces = get_namespaces(memory_client, memory_id)

    def retrieve_customer_context(self, event: MessageAddedEvent):
        """Retrieve relevant memories and prepend them to the user message."""
        messages = event.agent.messages
        if not messages:
            return

        last_message = messages[-1]
        if last_message.get("role") != "user":
            return

        content = last_message.get("content", [])
        if not content or "toolResult" in content[0]:
            return

        user_query = content[0].get("text", "")
        if not user_query:
            return

        all_memories = []
        for strategy_type, namespace_template in self.namespaces.items():
            namespace = namespace_template.format(actorId=self.actor_id)
            memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=namespace,
                query=user_query,
                top_k=5,
            )
            for m in memories:
                text = m.get("content", {}).get("text", "")
                if text:
                    all_memories.append(f"[{strategy_type}] {text}")

        if all_memories:
            context_block = "\n".join(all_memories)
            last_message["content"][0]["text"] = (
                f"Customer Context:\n{context_block}\n\n{user_query}"
            )

    def save_support_interaction(self, event: AfterInvocationEvent):
        """Save the completed turn to memory after the agent responds."""
        messages = event.agent.messages

        customer_query = None
        agent_response = None

        for message in reversed(messages):
            role = message.get("role")
            content = message.get("content", [])
            if not content:
                continue
            if "toolResult" in content[0] or "toolUse" in content[0]:
                continue
            text = content[0].get("text", "")
            if not text:
                continue
            if role == "assistant" and agent_response is None:
                agent_response = text
            elif role == "user" and customer_query is None:
                customer_query = text
            if customer_query and agent_response:
                break

        if customer_query and agent_response:
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[(customer_query, "USER"), (agent_response, "ASSISTANT")],
            )

    def register_hooks(self, registry: HookRegistry) -> None:  # type: ignore
        """Register both memory callbacks."""
        registry.add_callback(MessageAddedEvent, self.retrieve_customer_context)
        registry.add_callback(AfterInvocationEvent, self.save_support_interaction)

# ── TODO 6 — Knowledge Base Tool ─────────────────────────────────────────────
# Implement search_knowledge_base(query) using the @tool decorator.
#
# Steps:
#   1. Guard: if KB_ID is empty return "Knowledge base not configured."
#   2. Call _bedrock_runtime.retrieve(
#          knowledgeBaseId=KB_ID,
#          retrievalQuery={"text": query}
#      )
#   3. Extract resp["retrievalResults"]; return a message if empty
#   4. Join the text chunks with "\n---\n" and return the result
#
# The docstring is the tool description — the model uses it to decide when
# to call this tool, so keep it clear and accurate.

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the Amazon product catalog and support knowledge base.
    Use this for product specifications, return policies, warranty
    information, loyalty program details, and order status definitions.

    Args:
        query: The question or topic to search for

    Returns:
        Relevant information retrieved from the knowledge base
    """
    if not KB_ID or KB_ID == "<kbid>":
        return "Knowledge base not configured."

    resp = _bedrock_runtime.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
    )
    results = resp.get("retrievalResults", [])
    if not results:
        return f"No information found for: {query}"

    chunks = [r["content"]["text"] for r in results]
    return "\n---\n".join(chunks)


# ── TODO 7 — Loyalty Discount Tool (Code Interpreter) ────────────────────────
# Implement calculate_loyalty_discount() using the @tool decorator.
#
# The tool must:
#   1. Build a self-contained Python code string that:
#        • Defines earn_rates: {"standard": 1, "device": 2, "fresh": 5}
#        • Defines tier_rates: {"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}
#        • Calculates points_redeemed (floor to nearest 500, cap at 50% of order)
#        • Calculates tier_discount (applied to subtotal after points)
#        • Calculates final_total, total_savings, points_earned, remaining_points
#        • Prints a JSON result dict
#   2. Execute the code with code_session(REGION).invoke("executeCode", {...})
#      using language="python" and clearContext=True
#   3. Return the first result event as a JSON string
#   4. Include a fallback that computes only the tier discount if the
#      Code Interpreter is unavailable

@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:
    """
    Calculate the loyalty discount for a customer order using the
    AgentCore Code Interpreter. Runs exact arithmetic in a secure sandbox.

    Args:
        loyalty_points:   Customer's current points balance
        tier:             Customer tier — Silver, Gold, or Platinum
        order_total:      Order total in USD
        product_category: standard, device, or fresh

    Returns:
        Full discount breakdown and final price
    """
    code = f"""
import json

earn_rates = {{"standard": 1, "device": 2, "fresh": 5}}
tier_rates = {{"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}}

loyalty_points = {loyalty_points}
tier = "{tier}"
order_total = {order_total}
product_category = "{product_category}"

# Points redemption: 100 points = $1, floored to nearest 500 points,
# capped at 50% of the order total
max_redeemable_value = order_total * 0.5
max_points_by_value = int(max_redeemable_value * 100)
points_redeemed = min(loyalty_points, max_points_by_value)
points_redeemed = (points_redeemed // 500) * 500
points_discount_value = points_redeemed / 100

subtotal_after_points = order_total - points_discount_value

tier_discount_pct = tier_rates.get(tier, 0.00)
tier_discount_value = subtotal_after_points * tier_discount_pct

final_total = round(subtotal_after_points - tier_discount_value, 2)
total_savings = round(order_total - final_total, 2)

earn_rate = earn_rates.get(product_category, 1)
points_earned = int(final_total * earn_rate)
remaining_points = loyalty_points - points_redeemed + points_earned

result = {{
    "points_redeemed": points_redeemed,
    "tier_discount_pct": tier_discount_pct,
    "final_total": final_total,
    "total_savings": total_savings,
    "points_earned": points_earned,
    "remaining_points": remaining_points,
}}

print(json.dumps(result))
"""

    try:
        with code_session(REGION) as code_client:
            response = code_client.invoke("executeCode", {
                "code": code,
                "language": "python",
                "clearContext": True,
            })
        for event in response["stream"]:
            return json.dumps(event["result"])

    except Exception as e:
        logger.warning(f"Code Interpreter unavailable, using fallback: {e}")
        tier_rates = {"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}
        tier_discount_pct = tier_rates.get(tier, 0.00)
        final_total = round(order_total * (1 - tier_discount_pct), 2)
        fallback_result = {
            "points_redeemed": 0,
            "tier_discount_pct": tier_discount_pct,
            "final_total": final_total,
            "remaining_points": loyalty_points,
            "note": "Fallback calculation — Code Interpreter unavailable",
        }
        return json.dumps(fallback_result)


# ── TODO 8 — Agent Entrypoint ─────────────────────────────────────────────────
# Implement the invoke() function decorated with @app.entrypoint.
#
# Steps:
#   1. Extract user_input, actor_id, and session_id from the payload
#      (generate a UUID if session_id is missing)
#   2. Instantiate MemoryHook for this actor/session
#   3. Instantiate AgentCoreBrowser(region=REGION)
#   4. Build the tools list: [search_knowledge_base, calculate_loyalty_discount,
#                              agent_core_browser.browser]
#   5. Connect to the Gateway via MCPClient, load gateway_tools, extend tools list
#   6. Create and invoke the Agent with all tools, hooks, and system_prompt
#   7. Return the text from the first content block of the response
#   8. Handle exceptions gracefully

SYSTEM_PROMPT = """You are a helpful customer support AI assistant for an e-commerce platform.

You can help customers with:
- Tracking orders and checking order/customer details (via Gateway tools)
- Processing refunds and generating return labels (via Gateway tools)
- Answering product, policy, warranty, and loyalty programme questions (via search_knowledge_base)
- Calculating exact loyalty discounts on orders (via calculate_loyalty_discount)
- Browsing live web pages when asked to look something up online

Always use the appropriate tool rather than guessing. Be concise, friendly, and accurate.
If you don't have enough information to complete a request, ask a clarifying question."""


@app.entrypoint
async def invoke(payload, context=None):
    """
    Main handler called by AgentCore for every incoming request.

    Expected payload keys:
      prompt      (str, required) — the customer's message
      customer_id (str, optional) — unique customer identifier
      session_id  (str, optional) — session identifier; generated if absent
    """
    try:
        user_input = payload.get("prompt", "Hello!")
        actor_id = payload.get("customer_id", "anonymous")
        session_id = payload.get("session_id") or str(uuid.uuid4())

        memory_hook = MemoryHook(
            actor_id=actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=MEMORY_ID,
        )

        agent_core_browser = AgentCoreBrowser(region=REGION)

        tools = [
            search_knowledge_base,
            calculate_loyalty_discount,
            agent_core_browser.browser,
        ]

        gateway_client = MCPClient(
            lambda: streamable_http_client(url=GATEWAY_URL)
        )

        try:
            with gateway_client:
                gateway_tools = gateway_client.list_tools_sync()
                tools.extend(gateway_tools)

                agent = Agent(
                    model=model,
                    system_prompt=SYSTEM_PROMPT,
                    tools=tools,
                    hooks=[memory_hook],
                )

                response = agent(user_input)
                return response.message["content"][0]["text"]

        except (ConnectionError, TimeoutError) as gateway_err:
            logger.error(f"Gateway connection/timeout error: {gateway_err}")
            return (
                "I'm unable to reach our order-tracking and refund systems right now — "
                "the connection to our backend gateway timed out. Please try again in a "
                "moment. If this keeps happening, let support know the Gateway connection "
                "is unavailable."
            )

        except Exception as gateway_err:
            logger.error(f"Gateway or tool execution error: {gateway_err}")
            return (
                "I ran into a problem using one of our connected services (order tracking, "
                "refunds, or a related tool). Please try again, or rephrase your request — "
                "if the issue continues, this looks like a backend configuration problem "
                "worth reporting to support."
            )

    except Exception as e:
        logger.error(f"Error during invocation: {e}")
        return (
            "I'm sorry, something unexpected went wrong while processing your request. "
            "Please try again shortly."
        )


# ── CLI entry point (do not modify) ──────────────────────────────────────────
def main():
    """Run one invocation from the command line for local testing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=str)
    args = parser.parse_args()
    response = asyncio.run(invoke(json.loads(args.payload)))
    print(response)


if __name__ == "__main__":
    app.run()
    # Uncomment the line below and comment app.run() for local CLI testing:
    # main()
