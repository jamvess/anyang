"""Prompt frontmatter `defaults`: text for a declared input the caller leaves out.

Added for tutor_reply/v2 (specs/features/tutor/demo-room.md §2 C): v2 declares a new input,
`problem`, and callers of the v1 contract still send only `message`.
"""

from pathlib import Path

import pytest
import yaml

from app.ai.gateway import AIConfigError, AIInputError, Gateway
from app.ai.providers.fake import FakeProvider
from app.settings import get_settings

BODY = '<document name="problem">\n{{problem}}\n</document>\n<message>\n{{message}}\n</message>'


def make_gateway(tmp_path: Path, fake: FakeProvider, **meta: object) -> Gateway:
    folder = tmp_path / "tutor_reply"
    folder.mkdir(exist_ok=True)
    front = yaml.safe_dump({"purpose": "tutor_reply", "version": 1, **meta}, allow_unicode=True)
    (folder / "v1.md").write_text(f"---\n{front}---\n{BODY}\n", encoding="utf-8")
    config = get_settings().ai
    pinned = config.purposes["tutor_reply"].model_copy(update={"prompt": "v1"})
    config = config.model_copy(update={"purposes": {**config.purposes, "tutor_reply": pinned}})
    return Gateway(config=config, prompts_dir=tmp_path, provider=fake)


async def stream_prompt(gateway: Gateway, values: dict[str, str]) -> None:
    async for _ in gateway.stream("tutor_reply", values):
        pass


async def test_AI01_default_fills_a_left_out_input_and_a_given_value_wins(tmp_path):
    fake = FakeProvider({"tutor_reply": ["ok", "ok"]})
    gateway = make_gateway(
        tmp_path, fake, inputs=["problem", "message"], defaults={"problem": "none"}
    )

    await stream_prompt(gateway, {"message": "สวัสดี"})
    await stream_prompt(gateway, {"message": "ข้อนี้", "problem": "แยกตัวประกอบ"})

    first, second = (r.prompt for r in fake.requests)
    assert "none" in first and "สวัสดี" in first
    assert "แยกตัวประกอบ" in second and "none" not in second


async def test_AI01_inputs_without_a_default_are_still_required(tmp_path):
    gateway = make_gateway(
        tmp_path, FakeProvider({}), inputs=["problem", "message"], defaults={"problem": "none"}
    )

    with pytest.raises(AIInputError, match="message"):
        await stream_prompt(gateway, {})


@pytest.mark.parametrize(
    "defaults",
    [
        pytest.param({"other": "x"}, id="undeclared input"),
        pytest.param({"problem": 3}, id="not text"),
    ],
)
async def test_AI01_bad_defaults_are_a_config_error(tmp_path, defaults):
    gateway = make_gateway(
        tmp_path, FakeProvider({}), inputs=["problem", "message"], defaults=defaults
    )

    with pytest.raises(AIConfigError, match="defaults"):
        await stream_prompt(gateway, {"message": "x", "problem": "y"})
