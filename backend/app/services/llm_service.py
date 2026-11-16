
from groq import Groq

from backend.app.core.config import settings


# Initialize the Groq client.
client = Groq(
    api_key=settings.groq_api_key,
)


def generate_llm_response(
    system_prompt: str,
    user_prompt: str,
) -> str:

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
            max_completion_tokens=1024,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError("Groq returned an empty response.")

        return answer.strip()

    except Exception as exc:
        raise RuntimeError(
            "Failed to generate a response using Groq."
        ) from exc
