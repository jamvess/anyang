"""Text from a user or a file, for inside a data block of a prompt (CLAUDE.md rule 8). The
gateway applies this to every input by where its placeholder sits (prompt-data-blocks.md).

This keeps a closing tag from ending the block, including with spaces around the slash. It does
not list every look-alike (full-width signs, zero-width characters), because no list is complete
for a model that reads rather than parses. What limits the damage is elsewhere: the LLM writes to
nothing (CLAUDE.md rules 1, 2) and a prompt holds only the student's own data
(ai-orchestration §2.9).
"""

import re


def as_data(text: str, tag: str) -> str:
    """A closing `</tag>` in the text would end the block early and let the rest read as
    instructions, so its `<` becomes `&lt;`, which does not read as a tag. Every text that starts
    like that closing tag changes, `</tags>` too; everything else stays as it was."""
    closing = rf"<\s*/\s*{re.escape(tag)}"
    return re.sub(closing, lambda _: f"&lt;/{tag}", text, flags=re.IGNORECASE)


def as_attribute(text: str) -> str:
    """A value inside `name="…"` of a tag: anything that could close it, or start a new line of
    instructions, becomes a space."""
    return re.sub(r'["<>\r\n]', " ", text)
