"""Persona extract, gaps found in the self-review of PR #178 (specs/features/ai/persona-extract.md
· UM-05, UM-07). The reviewed files test_persona_extract_api.py and test_persona_merge.py are
not changed; this file reuses their helpers.
"""

import json

from app import stubs
from app.ai.gateway import get_gateway
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.models.persona import TutorParams
from tests.unit import test_persona_extract_api as api
from tests.unit.test_persona_extract_api import (
    EXTRACT,
    PRESETS,
    body,
    extract_answer,
    gateway_of,
    preview_answer,
    script,
)

client = api.client
fake = api.fake
no_retry_sleep = api.no_retry_sleep

BASE = TutorParams.model_validate(PRESETS["tutors"][0]["params"])


def test_UM05_fake_mode_answers_with_a_token_instead_of_503(client):
    # AI_PROVIDER=fake builds its provider with these defaults (app/ai/gateway.py).
    app.dependency_overrides[get_gateway] = lambda: gateway_of(
        FakeProvider({}, defaults=stubs.fake_persona())
    )

    response = client.post(EXTRACT, json=body())

    assert response.status_code == 200
    assert TutorParams.model_validate(response.json()["params"]) == BASE
    assert response.json()["sample"].endswith("(โหมด fake)")
    assert all(part.endswith("(โหมด fake)") for part in response.json()["refused"])


def test_UM05_a_key_the_schema_does_not_have_is_dropped_not_a_503(client, fake):
    answer = json.loads(extract_answer(energy=3))
    answer.update({"voice_id": "th-TH-Other-B", "gender": "female"})
    script(fake, [json.dumps(answer, ensure_ascii=False)], [preview_answer()])

    response = client.post(EXTRACT, json=body())

    assert response.status_code == 200
    params = TutorParams.model_validate(response.json()["params"])
    assert params == BASE.model_copy(update={"energy": 3})  # voice stays the preset's
