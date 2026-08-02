import anthropic


async def generate_code(prompt: str, language: str) -> tuple[str, str]:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=2048,
        system=(
            f"Write {language} code for the request. Respond with a fenced "
            f"code block, then a brief (2-3 sentence) explanation after it."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return _split_code_and_prose(text)


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
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system=f"Explain what this {language} code does, plainly, for a developer reading it cold.",
        messages=[{"role": "user", "content": code}],
    )
    return next(b.text for b in response.content if b.type == "text")


async def generate_tests(code: str, framework: str) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=2048,
        system=(
            f"Write {framework} unit tests for the given code. Cover the "
            f"normal case, at least one edge case, and error handling if "
            f"the code raises. Respond with only the test code, in a single "
            f"fenced code block."
        ),
        messages=[{"role": "user", "content": code}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    code_only, _ = _split_code_and_prose(text)
    return code_only or text.strip()
