"""
Standalone test script for SARVAM LLM API.
Used to verify conversational AI responses independently.
"""

import asyncio

from app.services.sarvam.llm_service import SarvamLLMService


async def main():
    """
    Run LLM response generation test.
    """

    llm_service = SarvamLLMService()

    response = await llm_service.generate_response(
        user_message="Can you tell me who is eligible for this event?"
    )

    print("\nLLM RESPONSE:\n")

    content = response["choices"][0]["message"]["content"]

    if "</think>" in content:
        content = content.split("</think>")[-1].strip()

    print(content)

if __name__ == "__main__":
    asyncio.run(main())