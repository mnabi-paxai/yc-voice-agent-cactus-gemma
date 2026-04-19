"""Twin Mind — Agent Loop

Shared tool-calling loop for all agent modes. Sends messages to Gemma 4
on Cactus, parses function calls, executes tools, and feeds results back
until the model produces a final text response.
"""

import json

from cactus import cactus_complete
from tools import TOOL_DEFINITIONS, execute_tool

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


def run_agent(model, system_prompt, user_message, data_dir, base_dir):
    """Run the agent loop until a final text response or max iterations."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tools_json = json.dumps(TOOL_DEFINITIONS)
    tool_results_collected = []

    for iteration in range(MAX_ITERATIONS):
        is_final_turn = len(tool_results_collected) > 0

        if is_final_turn:
            # After collecting tool results, ask the model to answer without tools
            context = "\n\n".join(
                f"[{r['tool']}] {r['content']}" for r in tool_results_collected
            )
            answer_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (
                    f"{user_message}\n\n"
                    f"Here is the information from the knowledge base:\n\n"
                    f"{context}\n\n"
                    f"Based on this information, answer the question concisely."
                )},
            ]
            options = {"max_tokens": 512, "temperature": 0.0}
            response_raw = cactus_complete(
                model,
                json.dumps(answer_messages),
                json.dumps(options),
                None,
                None,
            )
            try:
                result = json.loads(response_raw)
                return result.get("response", "").strip()
            except json.JSONDecodeError:
                return response_raw

        # Tool-calling turn
        options = {"max_tokens": 512, "temperature": 0.0, "force_tools": True}
        response_raw = cactus_complete(
            model,
            json.dumps(messages),
            json.dumps(options),
            tools_json,
            None,
        )

        try:
            result = json.loads(response_raw)
        except json.JSONDecodeError:
            return response_raw

        function_calls = result.get("function_calls", [])

        if not function_calls:
            text = result.get("response", "").replace("<|tool_call>", "").strip()
            if text:
                return text
            # No tool calls and no text — force a direct answer
            tool_results_collected.append({"tool": "note", "content": "No tools were called."})
            continue

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

            tool_results_collected.append({"tool": name, "content": tool_result})
            print(f"  [result] {tool_result[:120]}...")

    return "Agent could not produce a response."
