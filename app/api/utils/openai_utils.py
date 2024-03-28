# import asyncio
import json_repair
from openai import AsyncOpenAI

from app.core.config import OPENAIConfig, settings

gpt_35_turbo = AsyncOpenAI(
    api_key=OPENAIConfig.OPENAI_KEY,
)


async def generate_analysis(
    # moves: dict,
    # pgn_id: str,
    max_tokens: int = 500,
    # temperature: float = 0.25,
) -> str:
    """
    Generates answer based on the given question using the GPT-35 Turbo model.

    Args:
        question (str): The question to generate answer for.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 1500.
        temperature (float, optional): Controls randomness in the generation. Defaults to 0.25.

    Returns:
        str: The generated text.
    """
    response = await gpt_35_turbo.chat.completions.create(
        model="gpt-3.5-turbo",
        # response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": 'You are a helpful assistant. You will help answer their study doubts from grade and subject mentioned in prompt. Always answer in less than 5 sentences max and a minimum of one sentence. Also, tell whether the given question is an academic one or not, that is, whether it\'s course-related or not. If giving a maths equation, you can give it in latex which can easily be parsed in markdown for mobile, that is using $. You have to give a json response in the following json format: {"answer":"", "is_academic_question":bool}. Respond with JSON format strictly.',
            },
            {
                "role": "user",
                "content": "Grade: <grade>8</grade>, Subject: <subject>History</subject>, User question is: <question>Who was Babar?</question>.",
            },
        ],
        max_tokens=max_tokens,
    )
    # Convert the string response to a JSON object
    response_content = json_repair.loads(response.choices[0].message.content)

    return response_content  # Return the JSON object instead of a string


# Example usage:
# answer = asyncio.run(generate_analysis())

# print(answer)

# response = gpt_35_turbo.chat.completions.create(
#     model="gpt-35-turbo",
#     response_format={"type": "json_object"},
#     messages=prompt_messages,
#     max_tokens=1500,
#     extra_headers={
#         "Helicone-Auth": f"Bearer {settings.HELICONE_API_KEY}",
#         "Helicone-Target-Url": OPENAIConfig.AZURE_OPENAI_API_BASE,
#         "Helicone-Target-Provider": "Azure",
#         "Helicone-Property-agent_id": "zuai_community_agent",
#         "Helicone-User-Id": "zuai_community_user",
#     },
#     temperature=0.25,
# )

# response.choices[0].message.content
