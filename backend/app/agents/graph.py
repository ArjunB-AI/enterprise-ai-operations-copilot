
import logging

from langgraph.graph import StateGraph, START, END

from backend.app.agents.state import AgentState, AgentContext
from backend.app.agents.nodes import (
    classify_intent,
    knowledge_node,
    action_node,
)
from backend.app.agents.routing import route_by_intent


logger = logging.getLogger(__name__)


def build_agent_graph():

    logger.info("Building agent workflow graph.")

    try:
        graph_builder = StateGraph(
            AgentState,
            context_schema=AgentContext,
        )

        # Register the workflow nodes.
        graph_builder.add_node("classify_intent", classify_intent)
        graph_builder.add_node("knowledge", knowledge_node)
        graph_builder.add_node("action", action_node)

        logger.debug("Agent workflow nodes registered.")

        # Define the workflow entry point.
        graph_builder.add_edge(START, "classify_intent")

        # Route based on the classified intent.
        graph_builder.add_conditional_edges(
            "classify_intent",
            route_by_intent,
            {
                "knowledge": "knowledge",
                "action": "action",
            },
        )

        # Both paths finish the workflow.
        graph_builder.add_edge("knowledge", END)
        graph_builder.add_edge("action", END)

        logger.debug("Agent workflow edges configured.")

        agent = graph_builder.compile()

        logger.info("Agent workflow graph compiled successfully.")

        return agent

    except Exception:
        logger.exception("Failed to build agent workflow graph.")
        raise
