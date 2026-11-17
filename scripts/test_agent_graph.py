
import logging

from backend.app.core.logging import setup_logging
from backend.app.agents.graph import build_agent_graph

from backend.app.db.session import SessionLocal
from backend.app.db.vector_session import VectorSessionLocal


# Enable detailed logs for this diagnostic test.
setup_logging(level=logging.DEBUG)


logger = logging.getLogger(__name__)


logger.info("Starting standalone agent graph test.")

agent = build_agent_graph()

db = SessionLocal()
vector_db = VectorSessionLocal()


test_messages = [
    # Query that previously returned no relevant sources.
    "How can I replace my laptop?",

    # Query that previously retrieved a relevant document.
    "How can an employee get a laptop replaced?",

    # Action intent test.
    "Create a ticket because my laptop is not working.",
]


try:
    for index, message in enumerate(test_messages, start=1):

        print("\n" + "=" * 70)
        print(f"TEST CASE {index}: {message}")
        print("=" * 70)

        initial_state = {
            "user_message": message,
            "intent": "",
            "response": "",
            "sources": [],
        }

        logger.info("Invoking agent graph | test_case=%s", index)

        result = agent.invoke(
            initial_state,
            context={
                "db": db,
                "vector_db": vector_db,
            },
        )

        logger.info("Agent graph execution completed | test_case=%s", index)

        print(f"Employee Message: {message}")
        print(f"Detected Intent: {result['intent']}")
        print(f"Agent Response: {result['response']}")
        print(f"Sources: {result['sources']}")


except Exception:
    logger.exception("Standalone agent graph test failed.")
    raise

finally:
    db.close()
    vector_db.close()

    logger.info("Database sessions closed.")
    logger.info("Standalone agent graph test finished.")
