"""Twin Mind — Agent Loop

Shared tool-calling loop for all agent modes. Sends messages to Gemma 4
on Cactus, parses function calls, executes tools, and feeds results back
until the model produces a final text response.
"""

import json

from cactus import cactus_complete
from tools import execute_tool

MAX_ITERATIONS = 5


def _parse_function_call(fc):
    """Parse a function call from the response, handling both dict and string formats."""
    if isinstance(fc, str):
        try:
            fc = json.loads(fc)
        except json.JSONDecodeError:
            return None, {}

    name = fc.get("name", "")
    args = fc.get("arguments", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}

    return name, args


def run_agent(model, system_prompt, user_message, data_dir, base_dir, tools=None):
    """Run the agent loop: tool calls until the model gives a text answer."""
    from tools import TOOL_DEFINITIONS
    tool_defs = tools if tools is not None else TOOL_DEFINITIONS
    tools_json = json.dumps(tool_defs)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):
        options = {"max_tokens": 512, "temperature": 0.0}

        response_raw = cactus_complete(
            model, json.dumps(messages), json.dumps(options), tools_json, None,
        )

        try:
            result = json.loads(response_raw)
        except json.JSONDecodeError:
            return response_raw

        function_calls = result.get("function_calls", [])
        text_response = result.get("response", "").replace("<|tool_call>", "").strip()

        if not function_calls:
            return text_response

        for fc in function_calls:
            name, args = _parse_function_call(fc)
            if not name:
                continue

            print(f"  [tool] {name}({json.dumps(args)})")

            tool_result = execute_tool(
                name, args,
                data_dir=data_dir,
                base_dir=base_dir,
                model=model,
            )

            messages.append({"role": "assistant", "content": text_response})
            messages.append({
                "role": "tool",
                "content": json.dumps({"name": name, "content": tool_result}),
            })

            print(f"  [result] {tool_result[:150]}...")

    return text_response or "Agent reached maximum iterations without a final response."
