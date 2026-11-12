"""Self-review findings of PR #123 (specs/features/tutor/room-sessions-db.md): profile params
that are not a JSON object, a nickname equal to the fallback text, and the OpenAPI errors of
the room endpoints on the database (spec §6)."""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthContext, get_auth
from app.db.room import PrepRecord, ProfileFacts
from app.domain.room import FALLBACK_USER_NAME, BuddyFacts, room_names
from app.main import app
from app.services.room_db import greeting_of
from app.settings import get_settings

PRESET = "พี่ฟ้า"


@pytest.mark.parametrize("params", [[], "x", 3, ["name"], True])
def test_TM13_profile_params_that_are_not_an_object_fall_back_instead_of_500(params):
    names = room_names(
        nickname="นนท์",
        tutor_params=params,
        buddy=BuddyFacts(enabled=True, params=params),
        preset_tutor_name=PRESET,
    )

    assert names.tutor_name == PRESET
    assert names.buddy_name is None


def test_TM13_a_nickname_equal_to_the_fallback_text_is_greeted_by_name():
    today = date(2026, 11, 11)
    prep = PrepRecord(
        id=uuid.uuid4(),
        title="แคลคูลัส 1",
        exam_date=date(2026, 11, 20),
        active_scope_version_id=None,
    )
    templates = get_settings().messages.room_greeting

    named = greeting_of(
        prep, ProfileFacts(nickname=FALLBACK_USER_NAME, tutor_params=None, buddy=None), today
    )
    anonymous = greeting_of(prep, ProfileFacts(nickname=None, tutor_params=None, buddy=None), today)

    assert named.startswith(templates.hello_named.format(user_name=FALLBACK_USER_NAME))
    assert anonymous.startswith(templates.hello_anonymous.format())


@pytest.mark.parametrize(
    ("path", "method", "codes"),
    [
        ("/exam-preps/{id}/sessions/active", "get", {"404", "503"}),
        ("/exam-preps/{id}/sessions", "post", {"404", "503"}),
        ("/sessions/{id}", "get", {"404", "503"}),
        ("/sessions/{id}/messages", "get", {"404", "503"}),
        ("/sessions/{id}/messages", "post", {"404", "409", "429", "503"}),
    ],
)
def test_TM13_openapi_lists_the_db_errors_of_the_room(path, method, codes):
    responses = app.openapi()["paths"][path][method]["responses"]

    assert codes <= set(responses)
    assert "db_unavailable" in responses["503"]["description"]


@pytest.fixture
def signed_in_without_supabase(monkeypatch: pytest.MonkeyPatch):
    """A token (get_auth overridden) on a machine with no Supabase settings, like CI."""
    env = get_settings().env
    monkeypatch.setattr(env, "supabase_url", "")
    user = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="t")
    app.dependency_overrides[get_auth] = lambda: user
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_auth, None)


def test_TM13_a_room_request_that_never_reads_the_db_needs_no_supabase_settings(
    signed_in_without_supabase,
):
    """CI run 43152239753: the client was built when the dependency resolved, so an image
    message (old path, no DB) and a body failing validation got 500."""
    session_id = uuid.uuid4()
    image = {"image_path": f"t/sessions/{session_id}/x.jpg"}

    assert (
        signed_in_without_supabase.post(f"/sessions/{session_id}/messages", json=image).status_code
        == 200
    )
    assert (
        signed_in_without_supabase.post(f"/sessions/{session_id}/messages", json={}).status_code
        == 422
    )


def test_TM13_a_db_client_that_cannot_be_built_is_503_not_500(signed_in_without_supabase):
    response = signed_in_without_supabase.get(f"/sessions/{uuid.uuid4()}")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "db_unavailable"
