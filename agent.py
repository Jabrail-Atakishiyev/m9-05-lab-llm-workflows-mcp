"""
Lab | Build the Loop Yourself
Hand-rolled model→tool→model loop with short-term memory and a step limit.
No agent framework — plain Python only.
"""

import json
import os
import math
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Data & tools
# ---------------------------------------------------------------------------

with open("orders.json") as f:
    ORDERS: dict = json.load(f)


def lookup_order(order_id: str) -> dict:
    """Return order details for a given order ID, or an error dict."""
    order = ORDERS.get(order_id.upper())
    if order is None:
        return {"error": f"Order {order_id!r} not found."}
    return {"order_id": order_id.upper(), **order}


def calculate(expression: str) -> dict:
    """
    Safely evaluate a numeric expression string and return the result.
    Supports +  -  *  /  **  ()  and common math functions.
    """
    try:
        # Restrict the eval namespace to math functions only
        allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
        result = eval(expression, {"__builtins__": {}}, allowed)  # noqa: S307
        return {"expression": expression, "result": result}
    except Exception as exc:
        return {"error": str(exc)}


# Map tool name → Python function
TOOL_REGISTRY = {
    "lookup_order": lookup_order,
    "calculate": calculate,
}

# ---------------------------------------------------------------------------
# Gemini tool declarations
# ---------------------------------------------------------------------------

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="lookup_order",
                description="Look up an order by its ID and return item name, price, purchase date, and warranty period.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "order_id": types.Schema(
                            type="STRING",
                            description="The order ID, e.g. A1001",
                        )
                    },
                    required=["order_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="calculate",
                description="Evaluate a numeric expression and return the result. Use standard Python math syntax.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "expression": types.Schema(
                            type="STRING",
                            description="A numeric expression to evaluate, e.g. '1200 * 3'",
                        )
                    },
                    required=["expression"],
                ),
            ),
        ]
    )
]

# ---------------------------------------------------------------------------
# The hand-rolled agent loop
# ---------------------------------------------------------------------------

MAX_STEPS = 5


def run_turn(client: genai.Client, messages: list, user_input: str) -> str:
    """
    Append the user message, then run the tool-call loop until the model
    gives a final text answer (or the step limit is reached).

    Returns the assistant's final answer text and mutates `messages` in place
    so memory carries over to the next call.
    """
    # Append the new user message to shared memory
    messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

    for step in range(1, MAX_STEPS + 1):
        print(f"\n  [step {step}] calling model …")

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages,
            config=types.GenerateContentConfig(tools=TOOLS),
        )

        candidate = response.candidates[0]
        parts = candidate.content.parts

        # ── Does the model want to call a tool? ──────────────────────────
        tool_calls = [p for p in parts if p.function_call is not None]
        if tool_calls:
            # Append the model's reply (which contains the tool-call request)
            messages.append(types.Content(role="model", parts=parts))

            # Execute every requested tool and collect results
            result_parts = []
            for part in tool_calls:
                fc = part.function_call
                print(f"  [step {step}] tool call → {fc.name}({dict(fc.args)})")
                tool_fn = TOOL_REGISTRY[fc.name]
                tool_result = tool_fn(**fc.args)
                print(f"  [step {step}] tool result ← {tool_result}")

                result_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response=tool_result,
                        )
                    )
                )

            # Append the tool results to memory and continue the loop
            messages.append(types.Content(role="user", parts=result_parts))
            continue

        # ── Model returned a final text answer ───────────────────────────
        text_parts = [p.text for p in parts if p.text]
        final_answer = " ".join(text_parts).strip()
        # Append the model's final answer to memory
        messages.append(types.Content(role="model", parts=parts))
        return final_answer

    # Step limit hit
    return "⚠️  Couldn't finish in time (step limit reached)."


# ---------------------------------------------------------------------------
# Main — two-turn demo
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GOOGLE_API_KEY before running.")

    client = genai.Client(api_key=api_key)

    # Single shared messages list — this IS the short-term memory
    messages: list = []

    print("=" * 60)
    print("TURN 1")
    print("=" * 60)
    q1 = "What did order A1001 cost?"
    print(f"User: {q1}")
    answer1 = run_turn(client, messages, q1)
    print(f"\nAssistant: {answer1}")
    print(f"\n[memory now holds {len(messages)} message(s)]")

    print("\n" + "=" * 60)
    print("TURN 2  (memory test — 'three of them' refers to turn 1)")
    print("=" * 60)
    q2 = "And what about three of them?"
    print(f"User: {q2}")
    answer2 = run_turn(client, messages, q2)
    print(f"\nAssistant: {answer2}")
    print(f"\n[memory now holds {len(messages)} message(s)]")

    print("\n" + "=" * 60)
    print("MEMORY DUMP  (all messages in context)")
    print("=" * 60)
    for i, msg in enumerate(messages):
        role = msg.role.upper()
        for part in msg.parts:
            if part.text:
                print(f"  [{i}] {role}: {part.text[:120]}")
            elif part.function_call:
                fc = part.function_call
                print(f"  [{i}] {role} → tool_call: {fc.name}({dict(fc.args)})")
            elif part.function_response:
                fr = part.function_response
                print(f"  [{i}] {role} ← tool_result ({fr.name}): {fr.response}")


if __name__ == "__main__":
    main()
