"""Text from a user or a file, for inside a data block of a prompt (CLAUDE.md rule 8)."""

import re


def as_data(text: str, tag: str) -> str:
    """A closing `</tag>` in the text would end the block early and let the rest read as
    instructions, so it is broken. Everything else stays as it was."""
    return re.sub(rf"</\s*{tag}", rf"<\/{tag}", text, flags=re.IGNORECASE)
