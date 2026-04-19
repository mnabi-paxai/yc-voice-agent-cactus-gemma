"""Twin Mind — Agent Loop

Shared tool-calling loop for all agent modes. Sends messages to Gemma 4
on Cactus, parses function calls, executes tools, then generates a final
answer with the tool results as context.
"""

import json

from cactus import cactus_complete
from tools import execute_tool

MAX_TOOL_ROUNDS = 3


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
    """Two-phase agent: gather info with tools, then answer from context."""
    from tools import TOOL_DEFINITIONS
    tool_defs = tools if tools is not None else TOOL_DEFINITIONS
    tools_json = json.dumps(tool_defs)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Phase 1: Gather information via tool calls
    all_results = []
    for round_num in range(MAX_TOOL_ROUNDS):
        options = {"max_tokens": 256, "temperature": 0.0, "force_tools": True}
        response_raw = cactus_complete(
            model, json.dumps(messages), json.dumps(options), tools_json, None,
        )

        try:
            result = json.loads(response_raw)
        except json.JSONDecodeError:
            break

        function_calls = result.get("function_calls", [])
        if not function_calls:
            break

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
            all_results.append(f"[{name}] {tool_result}")
            print(f"  [result] {tool_result[:150]}...")

        # Only do one round of tool calls for now
        break

    # Phase 2: Generate answer with tool results as context
    if all_results:
        context = "\n\n".join(all_results)
        answer_prompt = (
            f"{user_message}\n\n"
            f"Here is what I found in the knowledge base:\n\n"
            f"{context}\n\n"
            f"Based on this information, provide a clear and concise answer."
        )
    else:
        answer_prompt = user_message

    answer_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": answer_prompt},
    ]
    options = {"max_tokens": 512, "temperature": 0.0}
    response_raw = cactus_complete(
        model, json.dumps(answer_messages), json.dumps(options), None, None,
    )

    try:
        result = json.loads(response_raw)
        answer = result.get("response", "")
        # Clean any stray tool call tokens
        answer = answer.split("<|tool_call>")[0].strip()
        if not answer:
            # If the model didn't produce text, return the tool results directly
            return "\n\n".join(all_results) if all_results else "No information found."
        return answer
    except json.JSONDecodeError:
        return response_raw
