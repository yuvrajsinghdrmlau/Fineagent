"""
agent.py
--------
This is the agent loop: the part that makes this project "agentic"
rather than a single prompt-response call.

The flow (perceive -> plan -> act -> observe -> respond) works like this:
  1. User asks a question.
  2. We send it to Claude along with the list of available tools.
  3. Claude decides (on its own) whether it needs to call a tool to answer,
     and if so, which one and with what arguments.
  4. We execute that tool in Python and send the result back to Claude.
  5. Claude reads the result and either calls another tool (multi-step
     reasoning) or gives a final answer.

This loop can run for multiple turns - that's what separates an "agent"
from a plain chatbot: it can chain several tool calls together to
answer one question.
"""

import os
import anthropic
from app.tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

MODEL = "claude-sonnet-4-6"  # swap for whichever model you have access to

SYSTEM_PROMPT = """You are FinAgent, a personal finance assistant with access to
the user's transaction data through tools. You are not just answering from
general knowledge - you must use the tools to look up real numbers before
answering any question about the user's spending, budget, or transactions.

Guidelines:
- Always call a tool before making any factual claim about the user's finances.
- If a question requires multiple pieces of information (e.g. spending AND a
  budget check), call multiple tools in sequence before giving your final answer.
- When you notice something worth flagging (e.g. an anomaly), mention it even
  if the user didn't explicitly ask, but keep it brief.
- Keep your final answers concise and practical - this is a finance tracker,
  not an essay generator.
- Currency is Indian Rupees (₹).
"""


def run_agent(user_message: str, max_turns: int = 5, verbose: bool = True) -> str:
    """
    Runs the agent loop for a single user message and returns the final
    text answer. Set verbose=True to see the agent's tool calls printed
    to the console - this is genuinely useful for demoing "agentic
    reasoning" in an interview or a LinkedIn video.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    messages = [{"role": "user", "content": user_message}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Collect any tool_use blocks the model wants to execute
        tool_calls = [block for block in response.content if block.type == "tool_use"]

        if not tool_calls:
            # No more tools needed - this is the final answer
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return final_text

        # The model wants to use one or more tools - append its turn, then
        # execute each tool call and append the results as a new "user" turn.
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for call in tool_calls:
            if verbose:
                print(f"[agent] calling tool: {call.name}({call.input})")

            fn = TOOL_FUNCTIONS.get(call.name)
            try:
                result = fn(**call.input) if fn else {"error": "unknown tool"}
            except Exception as e:
                result = {"error": str(e)}

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": str(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return "I reasoned through several steps but couldn't finish in time. Try rephrasing your question."


if __name__ == "__main__":
    # Quick manual test: python -m app.agent
    from app.db import init_db
    from app.parser import load_statement

    init_db()
    load_statement("sample_data/transactions.csv")

    while True:
        q = input("\nAsk FinAgent something (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = run_agent(q)
        print(f"\nFinAgent: {answer}")
