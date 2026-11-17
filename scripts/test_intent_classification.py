
from backend.app.agents.nodes import classify_intent


test_messages = [
    "How can I replace my laptop?",
    "What is the company password policy?",
    "Create a ticket because my laptop is not working.",
    "I need access to a new application.",
]


for message in test_messages:

    state = {
        "user_message": message,
        "intent": "",
        "response": "",
        "sources": [],
    }

    result = classify_intent(state)

    print(f"\nMessage: {message}")
    print(f"Intent: {result['intent']}")
