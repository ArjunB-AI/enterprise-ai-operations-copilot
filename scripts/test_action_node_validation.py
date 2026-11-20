
import logging
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.agents.nodes import action_node


logging.basicConfig(level=logging.INFO)


def create_tool_call(name: str, arguments: str):
    """Create a simulated Groq tool call."""
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def run_test(test_name: str, tool_calls: list):
    """Run action_node with a simulated Groq response."""

    print("\n" + "=" * 65)
    print(f"TEST: {test_name}")
    print("=" * 65)

    mock_message = SimpleNamespace(
        tool_calls=tool_calls,
        content=None,
    )

    # These validation tests should reject the request before
    # accessing the database or executing any ticket tool.
    runtime = SimpleNamespace(context={})

    with patch(
        "backend.app.agents.nodes.generate_tool_call",
        return_value=mock_message,
    ):
        result = action_node(
            state={
                "user_message": "Test employee action request",
                "intent": "action",
                "response": "",
                "sources": [],
            },
            runtime=runtime,
        )

    print("Agent response:", result["response"])

    return result


def main():

    # TEST 1: Multiple tool calls
    result = run_test(
        "Multiple tool calls",
        [
            create_tool_call(
                "get_employee_tickets",
                "{}",
            ),
            create_tool_call(
                "create_employee_ticket",
                '{"ticket_type": "incident"}',
            ),
        ],
    )

    assert "safely" in result["response"].lower()
    print("PASS: Multiple tool calls rejected.")

    # TEST 2: Malformed JSON
    result = run_test(
        "Malformed JSON arguments",
        [
            create_tool_call(
                "create_employee_ticket",
                '{"ticket_type": "incident"',
            ),
        ],
    )

    assert "understand" in result["response"].lower()
    print("PASS: Malformed JSON rejected.")

    # TEST 3: Invalid ticket fields
    result = run_test(
        "Invalid ticket fields",
        [
            create_tool_call(
                "create_employee_ticket",
                '{"ticket_type": "invalid", '
                '"title": "Test ticket", '
                '"description": "Test description"}',
            ),
        ],
    )

    assert "invalid or missing" in result["response"].lower()
    print("PASS: Invalid ticket fields rejected.")

    # TEST 4: Unexpected arguments for ticket retrieval
    result = run_test(
        "Unexpected retrieval arguments",
        [
            create_tool_call(
                "get_employee_tickets",
                '{"user_id": 123}',
            ),
        ],
    )

    assert "couldn't process" in result["response"].lower()
    print("PASS: Unexpected retrieval arguments rejected.")

    # TEST 5: Unsupported tool name
    result = run_test(
        "Unsupported tool name",
        [
            create_tool_call(
                "delete_all_tickets",
                "{}",
            ),
        ],
    )

    assert "couldn't process" in result["response"].lower()
    print("PASS: Unsupported tool name rejected.")

    print("\n" + "=" * 65)
    print("ALL VALIDATION TESTS PASSED")
    print("=" * 65)


if __name__ == "__main__":
    main()
