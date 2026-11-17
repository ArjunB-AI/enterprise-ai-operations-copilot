
import logging

from langgraph.runtime import Runtime

from backend.app.agents.state import AgentState, AgentContext
from backend.app.services.llm_service import generate_llm_response
from backend.app.services.rag_service import generate_rag_response


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

    2. action:
       Requests to perform an operation, such as
       creating a ticket, reporting an incident,
       requesting an asset, or requesting access.

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


def action_node(state: AgentState) -> dict:

    logger.info("Action node started.")

    response = (
        "I understand that you want to perform an IT operation. "
        "Action execution is not available yet. "
        "Please try again after the backend tools are integrated."
    )

    logger.info("Action node completed | execution_available=False")

    return {
        "response": response,
        "sources": [],
    }
