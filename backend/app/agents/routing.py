
import logging

from backend.app.agents.state import AgentState


logger = logging.getLogger(__name__)


def route_by_intent(state: AgentState) -> str:

    intent = state["intent"]

    logger.info(
        "Agent routing started | detected_intent=%s",
        intent,
    )

    if intent == "knowledge":
        logger.info("Agent route selected | destination=knowledge")
        return "knowledge"

    if intent == "action":
        logger.info("Agent route selected | destination=action")
        return "action"

    logger.error(
        "Agent routing failed | unsupported_intent=%s",
        intent,
    )

    raise ValueError(f"Unsupported intent: {intent}")
