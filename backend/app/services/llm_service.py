
import logging
import time

from groq import Groq

from backend.app.core.config import settings


logger = logging.getLogger(__name__)


# Initialize the Groq client.
client = Groq(
    api_key=settings.groq_api_key,
)


def generate_llm_response(
    system_prompt: str,
    user_prompt: str,
) -> str:

    logger.info(
        "LLM request started | model=%s | system_prompt_chars=%s | user_prompt_chars=%s",
        settings.groq_model,
        len(system_prompt),
        len(user_prompt),
    )

    start_time = time.perf_counter()

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

        elapsed_time = time.perf_counter() - start_time

        usage = response.usage

        logger.info(
            "LLM response received | model=%s | duration_seconds=%.2f | prompt_tokens=%s | completion_tokens=%s",
            settings.groq_model,
            elapsed_time,
            usage.prompt_tokens if usage else None,
            usage.completion_tokens if usage else None,
        )

        return answer.strip()

    except Exception:
        elapsed_time = time.perf_counter() - start_time

        logger.exception(
            "LLM request failed | model=%s | duration_seconds=%.2f",
            settings.groq_model,
            elapsed_time,
        )

        raise RuntimeError(
            "Failed to generate a response using Groq."
        ) from None
