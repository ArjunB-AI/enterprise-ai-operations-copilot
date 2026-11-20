import logging
from pydantic import ValidationError
from langgraph.runtime import Runtime

from backend.app.agents.state import AgentState, AgentContext
from backend.app.services.rag_service import generate_rag_response

import json

from backend.app.agents.tools.tool_schemas import TICKET_TOOL_SCHEMAS
from backend.app.agents.tools.ticket_tools import (
    create_employee_ticket,
    get_employee_tickets,
)
from backend.app.services.llm_service import (
    generate_llm_response,
    generate_tool_call,
)
from backend.app.schemas.ticket import TicketCreate


logger = logging.getLogger(__name__)


def classify_intent(state: AgentState) -> dict:

    logger.info("Intent classification started.")

    
    system_prompt = """
    You are an intent classification system for an
    Enterprise IT Operations Assistant.

    Classify the employee's message into exactly one
    of these categories:

    1. knowledge:
    Questions asking for information, explanations,
    company policies, IT procedures, or guidance.

    Examples:
    - What is the laptop replacement policy?
    - How do I request access?
    - What should I do if I forget my password?

    2. action:
    Requests that require retrieving or performing
    an operation using the employee's account.

    Examples:
    - Create a ticket for my laptop issue.
    - Report that my laptop is not working.
    - Show me all my tickets.
    - What is the status of my ticket?
    - Show my open tickets.
    - List my previous IT requests.

    Important:
    - Retrieving the employee's own tickets is an action.
    - Checking ticket status is an action.
    - Do not classify personal ticket retrieval as knowledge.

    Return only one word:
    knowledge
    or
    action

    Do not provide explanations or additional text.
    """


    user_prompt = state["user_message"]

    try:
        intent = generate_llm_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        ).strip().lower()

        if intent not in {"knowledge", "action"}:
            logger.error(
                "Intent classification returned invalid value | intent=%s",
                intent,
            )
            raise ValueError(
                f"Invalid intent returned by LLM: {intent}"
            )

        logger.info(
            "Intent classification completed | intent=%s",
            intent,
        )

        return {"intent": intent}

    except Exception:
        logger.exception("Intent classification failed.")
        raise


def knowledge_node(
    state: AgentState,
    runtime: Runtime[AgentContext],
) -> dict:

    logger.info("Knowledge node started.")

    try:
        rag_result = generate_rag_response(
            query=state["user_message"],
            db=runtime.context["db"],
            vector_db=runtime.context["vector_db"],
        )

        logger.info(
            "Knowledge node completed | source_count=%s",
            len(rag_result["sources"]),
        )

        return {
            "response": rag_result["answer"],
            "sources": rag_result["sources"],
        }

    except Exception:
        logger.exception("Knowledge node failed.")
        raise



def action_node(
    state: AgentState,
    runtime: Runtime[AgentContext],
) -> dict:

    logger.info("Action node started.")

    system_prompt = """
    You are an IT Operations Assistant for company employees.

    You can perform these operations:

    1. Create an IT ticket when an employee reports an issue
       or requests IT assistance.

    2. Retrieve the authenticated employee's own tickets
       when they ask about their tickets or ticket status.

    Rules:
    - Use the appropriate tool when an operation is requested.
    - Never invent ticket details.
    - Never ask for or accept an employee ID.
    - The authenticated employee context is provided by the backend.
    - If required ticket details are missing, ask the employee
      for the missing information instead of creating a ticket.
    - Do not claim an operation succeeded unless the tool
      actually executed successfully.
    """

    try:
        message = generate_tool_call(
            system_prompt=system_prompt,
            user_prompt=state["user_message"],
            tools=TICKET_TOOL_SCHEMAS,
        )

        if not message.tool_calls:
            response = message.content or (
                "Could you provide more details about "
                "the IT operation you need?"
            )

            logger.info(
                "Action node completed | tool_executed=False"
            )

            return {
                "response": response,
                "sources": [],
            }

                # Reject multiple tool calls to prevent accidental
        # duplicate or uncontrolled operations.
        if len(message.tool_calls) != 1:
            logger.warning(
                "Multiple tool calls rejected | tool_count=%s",
                len(message.tool_calls),
            )

            return {
                "response": (
                    "I couldn't process that operation safely. "
                    "Please try one request at a time."
                ),
                "sources": [],
            }

        tool_call = message.tool_calls[0]

        tool_name = tool_call.function.name
        try:
            tool_arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received in tool arguments.")

            return {
                "response": (
                    "I couldn't understand the requested operation. "
                    "Please try again."
                ),
                "sources": [],
            }

        if not isinstance(tool_arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        if tool_name == "create_employee_ticket":
            ticket_data = TicketCreate.model_validate(
                tool_arguments
            )

            tool_arguments = ticket_data.model_dump()

        elif tool_name == "get_employee_tickets":
            if tool_arguments:
                raise ValueError(
                    "get_employee_tickets does not accept arguments."
                )

        else:
            raise ValueError(
                f"Unsupported tool requested: {tool_name}"
            )

        db = runtime.context["db"]
        current_user = runtime.context["current_user"]

        if current_user.role != "employee":
            raise PermissionError(
                "Only employees can use these agent tools."
            )

        logger.info(
            "Executing employee tool | tool_name=%s | user_id=%s",
            tool_name,
            current_user.id,
        )

        if tool_name == "create_employee_ticket":

            ticket = create_employee_ticket(
                db=db,
                current_user=current_user,
                **tool_arguments,
            )

            response = (
                "Your IT ticket has been created successfully.\n\n"
                f"**Ticket ID:** {ticket.id}\n"
                f"**Title:** {ticket.title}\n"
                f"**Type:** {ticket.ticket_type}\n"
                f"**Priority:** {ticket.priority}\n"
                f"**Status:** {ticket.status}"
            )

        elif tool_name == "get_employee_tickets":

            tickets = get_employee_tickets(
                db=db,
                current_user=current_user,
            )

            if not tickets:
                response = "You don't have any IT tickets yet."
            else:
                ticket_details = []

                for ticket in tickets:
                    ticket_details.append(
                        f"Ticket ID: {ticket.id}\n"
                        f"Title: {ticket.title}\n"
                        f"Status: {ticket.status}\n"
                        f"Priority: {ticket.priority}"
                    )

                response = (
                    "Here are your IT tickets:\n\n"
                    + "\n\n".join(ticket_details)
                )

        else:
            raise ValueError(
                f"Unsupported tool requested: {tool_name}"
            )

        logger.info(
            "Action node completed | tool_name=%s | user_id=%s",
            tool_name,
            current_user.id,
        )

        return {
            "response": response,
            "sources": [],
        }

    except ValidationError:
        logger.warning("Invalid ticket data received from tool call.")

        return {
            "response": (
                "Some ticket details are invalid or missing. "
                "Please provide valid ticket information."
            ),
            "sources": [],
        }

    except ValueError as exc:
        logger.warning("Invalid tool arguments | error=%s", exc)

        return {
            "response": (
                "I couldn't process that request because it contains "
                "unexpected or invalid arguments."
            ),
            "sources": [],
        }

    except Exception:
        logger.exception("Action node failed.")
        raise

