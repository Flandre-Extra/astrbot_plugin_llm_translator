import re

BRACKET_RE = re.compile(
    r"（[^（）]*）|\([^()]*\)|【[^【】]*】|\[[^\[\]]*\]|「[^「」]*」|『[^『』]*』"
)


def strip_brackets(text: str) -> str:
    for _ in range(5):
        prev = text
        text = BRACKET_RE.sub("", text)
        if text == prev:
            break
    return text.strip()
