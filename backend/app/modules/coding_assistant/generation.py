from app.providers.factory import get_provider
from app.providers.types import AIMessage


async def generate_code(prompt: str, language: str) -> tuple[str, str]:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=prompt)],
        system=(
            f"Write {language} code for the request. Respond with a fenced "
            f"code block, then a brief (2-3 sentence) explanation after it."
        ),
        max_tokens=2048,
    )
    return _split_code_and_prose(response.text)


def _split_code_and_prose(text: str) -> tuple[str, str]:
    if "```" not in text:
        return text.strip(), ""
    parts = text.split("```")
    # parts: [before, "lang\ncode", after, ...] — take the first fenced block
    code_block = parts[1]
    code = code_block.split("\n", 1)[1] if "\n" in code_block else code_block
    explanation = (parts[2] if len(parts) > 2 else "").strip()
    return code.strip(), explanation


async def explain_code(code: str, language: str) -> str:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=code)],
        system=f"Explain what this {language} code does, plainly, for a developer reading it cold.",
        max_tokens=1024,
    )
    return response.text


async def generate_tests(code: str, framework: str) -> str:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=code)],
        system=(
            f"Write {framework} unit tests for the given code. Cover the "
            f"normal case, at least one edge case, and error handling if "
            f"the code raises. Respond with only the test code, in a single "
            f"fenced code block."
        ),
        max_tokens=2048,
    )
    code_only, _ = _split_code_and_prose(response.text)
    return code_only or response.text.strip()
