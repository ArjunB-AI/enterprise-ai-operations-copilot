
from backend.app.services.llm_service import generate_llm_response


def main():
    system_prompt = """
    You are an IT support assistant.
    Give clear and simple answers.
    """

    user_prompt = "What is an IT asset? Explain in two sentences."

    print("Sending request to Groq...\n")

    response = generate_llm_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    print("Groq Response:")
    print(response)


if __name__ == "__main__":
    main()
