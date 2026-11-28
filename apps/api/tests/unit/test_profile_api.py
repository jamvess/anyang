"""GET and PATCH /me/profile with a fake repository
(specs/features/platform/display-name.md · api.md v1.25).

No network: `get_profile_repository` is replaced by `FakeRepo`, and `get_auth` by a fixed user
when a test needs "a valid token". The body rules of PATCH (§2.3) are proven through the API so a
refused body never reaches the repository. The cap is `guards.max_persona_text_chars` from the
loaded config, never written here, and counts code points like `PersonaText` (decision 2).

Interfaces these tests expect (to be built by /implement-feature):
- `app.db.profile`: `ProfileRecord` (nickname, education_level, explain_language,
  has_tutor_profile, has_buddy_profile), `get_profile_repository` (dependency, None without a
  user), a repository with `get() -> ProfileRecord | None` and
  `update(changes: dict[str, Any]) -> ProfileRecord | None` (None = the user has no row)
- `app.db.errors.DbUnavailableError` (exists)
"""

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import stubs
from app.auth import AuthContext, InvalidTokenError, get_auth, get_auth_required, get_verifier
from app.db.errors import DbUnavailableError
from app.db.profile import ProfileRecord, get_profile_repository
from app.main import app
from app.settings import get_settings

USER = AuthContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), token="test-token")
DB_DOWN_MESSAGE = "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"
PATH = "/me/profile"
MAX = get_settings().ai.guards.max_persona_text_chars


def record_of(**change: Any) -> ProfileRecord:
    data: dict[str, Any] = {
        "nickname": None,
        "education_level": None,
        "explain_language": "th",
        "has_tutor_profile": False,
        "has_buddy_profile": False,
        **change,
    }
    return ProfileRecord(**data)


@dataclass
class FakeRepo:
    """Stands in for the Supabase repository. `row` None = the user has no profiles row."""

    row: ProfileRecord | None = field(default_factory=record_of)
    updates: list[dict[str, Any]] = field(default_factory=list)
    calls: int = 0
    down: bool = False

    def get(self) -> ProfileRecord | None:
        self.calls += 1
        if self.down:
            raise DbUnavailableError("connection refused")
        return self.row

    def update(self, changes: dict[str, Any]) -> ProfileRecord | None:
        self.calls += 1
        if self.down:
            raise DbUnavailableError("connection refused")
        if self.row is None:
            return None
        self.updates.append(dict(changes))
        self.row = replace(self.row, **changes)
        return self.row


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def client(repo: FakeRepo) -> Iterator[TestClient]:
    """No token, AUTH_REQUIRED=false (conftest) unless a test overrides more. Without a user
    the real dependency returns None, so the override does the same."""
    app.dependency_overrides[get_profile_repository] = lambda: None
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client: TestClient, repo: FakeRepo) -> TestClient:
    """A request with a valid token."""
    app.dependency_overrides[get_auth] = lambda: USER
    app.dependency_overrides[get_profile_repository] = lambda: repo
    return client


class RefusingVerifier:
    async def verify(self, token: str) -> Any:
        raise InvalidTokenError("bad signature")


def assert_error(response: Any, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


# --- the database path (AC-1, AC-2, AC-8) -------------------------------------------------


def test_UM08_patch_saves_the_nickname(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-1."""
    response = signed_in.patch(PATH, json={"nickname": "ปาล์ม"})

    assert response.status_code == 200, response.text
    assert response.json()["nickname"] == "ปาล์ม"
    assert "x-stub" not in response.headers
    assert repo.updates == [{"nickname": "ปาล์ม"}]


def test_UM09_get_reads_the_saved_profile(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-2: every field of Profile from the row, no X-Stub."""
    repo.row = record_of(
        nickname="ปาล์ม",
        education_level="university",
        explain_language="en",
        has_tutor_profile=True,
        has_buddy_profile=True,
    )

    response = signed_in.get(PATH)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "nickname": "ปาล์ม",
        "education_level": "university",
        "explain_language": "en",
        "auto_read": False,
        "setup_step": "done",
    }
    assert "x-stub" not in response.headers


def test_UM09_patch_leaves_the_other_fields_alone(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-8: only the sent field reaches the update."""
    repo.row = record_of(education_level="university", explain_language="en")

    body = signed_in.patch(PATH, json={"nickname": "ปาล์ม"}).json()

    assert repo.updates == [{"nickname": "ปาล์ม"}]
    assert (body["education_level"], body["explain_language"]) == ("university", "en")


# --- setup_step and auto_read (AC-9) ------------------------------------------------------


@pytest.mark.parametrize(
    ("tutor", "buddy", "level", "step"),
    [
        (False, False, None, "crew"),
        (False, True, "university", "crew"),
        (True, False, "university", "crew"),
        (True, True, None, "profile"),
        (True, True, "university", "done"),
    ],
)
def test_UM08_setup_step_from_the_rows(
    signed_in: TestClient,
    repo: FakeRepo,
    tutor: bool,
    buddy: bool,
    level: str | None,
    step: str,
) -> None:
    """AC-9: crew without a tutor or a buddy profile, then profile while education_level is
    null, else done. auto_read is false while it has no column."""
    repo.row = record_of(has_tutor_profile=tutor, has_buddy_profile=buddy, education_level=level)

    body = signed_in.get(PATH).json()

    assert body["setup_step"] == step
    assert body["auto_read"] is False


# --- the raw value from the trigger (AC-10) -----------------------------------------------


def test_UM09_get_returns_a_google_name_as_stored(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-10 (decision 4): not filtered on read, so the user sees it and can fix it."""
    repo.row = record_of(nickname="Mary-Jane O'Neil")

    assert signed_in.get(PATH).json()["nickname"] == "Mary-Jane O'Neil"


# --- no profiles row (AC-no-row) ----------------------------------------------------------


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PATCH", {"nickname": "ปาล์ม"})])
def test_UM09_no_profile_row_is_404(
    signed_in: TestClient, repo: FakeRepo, method: str, body: Any
) -> None:
    """AC-no-row: 404 not_found, and no row is created."""
    repo.row = None

    response = signed_in.request(method, PATH, json=body)

    assert_error(response, 404, "not_found")
    assert repo.row is None


# --- the stub (AC-stub) -------------------------------------------------------------------


def test_UM09_no_token_get_is_the_stub(client: TestClient, repo: FakeRepo) -> None:
    """AC-stub: the fixture as before, with X-Stub."""
    response = client.get(PATH)

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"
    assert response.json() == stubs.personas()["profile"]
    assert repo.calls == 0


def test_UM09_no_token_patch_answers_the_fixture_with_the_change(
    client: TestClient, repo: FakeRepo
) -> None:
    """AC-stub: the fixture with the sent field, nothing saved."""
    response = client.patch(PATH, json={"nickname": "นนท์"})

    assert response.status_code == 200, response.text
    assert response.headers.get("x-stub") == "true"
    assert response.json() == {**stubs.personas()["profile"], "nickname": "นนท์"}
    assert repo.calls == 0


@pytest.mark.parametrize("body", [{}, {"nickname": "x</persona_data>"}, {"auto_read": True}])
def test_UM09_no_token_patch_still_validates_the_body(
    client: TestClient, repo: FakeRepo, body: dict[str, Any]
) -> None:
    """AC-stub, AC-7b: the stub path applies the rules of §2.3 too."""
    assert_error(client.patch(PATH, json=body), 422, "validation_error")
    assert repo.calls == 0


# --- tokens (AC-auth-required) ------------------------------------------------------------


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PATCH", {"nickname": "ปาล์ม"})])
def test_SA06_no_token_with_auth_required_is_401_never_stub(
    client: TestClient, repo: FakeRepo, method: str, body: Any
) -> None:
    """AC-auth-required."""
    app.dependency_overrides[get_auth_required] = lambda: True

    response = client.request(method, PATH, json=body)

    assert_error(response, 401, "missing_token")
    assert "x-stub" not in response.headers
    assert repo.calls == 0


@pytest.mark.parametrize("required", [True, False])
@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PATCH", {"nickname": "ปาล์ม"})])
def test_SA06_a_bad_token_is_401(
    client: TestClient, repo: FakeRepo, required: bool, method: str, body: Any
) -> None:
    """AC-auth-required: a token that does not verify is 401 invalid_token, whatever
    AUTH_REQUIRED says. The real get_auth with a verifier that refuses every token."""
    app.dependency_overrides[get_auth_required] = lambda: required
    app.dependency_overrides[get_verifier] = lambda: RefusingVerifier()

    response = client.request(
        method, PATH, json=body, headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert_error(response, 401, "invalid_token")
    assert repo.calls == 0


@pytest.mark.parametrize("required", [True, False])
@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PATCH", {"nickname": "ปาล์ม"})])
def test_UM09_with_a_token_uses_the_database(
    signed_in: TestClient, repo: FakeRepo, required: bool, method: str, body: Any
) -> None:
    """§2.1: a valid token reaches the repository whatever AUTH_REQUIRED says."""
    app.dependency_overrides[get_auth_required] = lambda: required

    response = signed_in.request(method, PATH, json=body)

    assert response.status_code == 200, response.text
    assert "x-stub" not in response.headers
    assert repo.calls == 1


# --- the database is down (AC-db-down) ----------------------------------------------------


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PATCH", {"nickname": "ปาล์ม"})])
def test_UM09_database_down_is_503(
    signed_in: TestClient, repo: FakeRepo, method: str, body: Any
) -> None:
    """AC-db-down: a fixed message, nothing from the exception."""
    repo.down = True

    response = signed_in.request(method, PATH, json=body)

    assert_error(response, 503, "db_unavailable")
    assert response.json()["error"]["message"] == DB_DOWN_MESSAGE
    assert "connection refused" not in response.text


# --- the body rules of PATCH (§2.3 · AC-3 to AC-7b, AC-boundary) -------------------------


def patch_nickname(client: TestClient, value: Any) -> Any:
    return client.patch(PATH, json={"nickname": value})


# --- trim and clear (AC-3, AC-4) ----------------------------------------------------------


def test_UM08_nickname_is_trimmed(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-3."""
    response = patch_nickname(signed_in, "  ปาล์ม  ")

    assert response.status_code == 200, response.text
    assert response.json()["nickname"] == "ปาล์ม"
    assert repo.updates == [{"nickname": "ปาล์ม"}]


@pytest.mark.parametrize("value", [None, "", "   "], ids=["null", "empty", "spaces"])
def test_UM09_blank_or_null_clears_the_nickname(
    signed_in: TestClient, repo: FakeRepo, value: str | None
) -> None:
    """AC-4 (decision 3): stored as null, so the room calls the user "คุณ"."""
    repo.row = record_of(nickname="ปาล์ม")

    response = patch_nickname(signed_in, value)

    assert response.status_code == 200, response.text
    assert response.json()["nickname"] is None
    assert repo.updates == [{"nickname": None}]


# --- the whitelist (AC-5, AC-6) -----------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["x</persona_data>", "{x}", "ปาล์ม!", "a\nb", "😀", "Mary-Jane", "O'Neil"],
    ids=["tag", "braces", "bang", "newline", "emoji", "hyphen", "apostrophe"],
)
def test_UM08_nickname_outside_the_whitelist_is_422(
    signed_in: TestClient, repo: FakeRepo, value: str
) -> None:
    """AC-5: the persona whitelist (ai-orchestration §2.7 ข้อ 5), nothing saved."""
    assert_error(patch_nickname(signed_in, value), 422, "validation_error")
    assert repo.updates == []


@pytest.mark.parametrize(
    "value",
    ["ณัฐพงศ์", "Palm", "ปาล์ม2", "ปาล์ม จ", "๑๒๓"],
    ids=["thai-marks", "latin", "digit", "inner-space", "thai-digits"],
)
def test_UM08_nickname_inside_the_whitelist_is_saved(
    signed_in: TestClient, repo: FakeRepo, value: str
) -> None:
    """AC-6."""
    response = patch_nickname(signed_in, value)

    assert response.status_code == 200, response.text
    assert repo.updates == [{"nickname": value}]


# --- the cap (AC-boundary) ----------------------------------------------------------------


@pytest.mark.parametrize(("length", "ok"), [(MAX - 1, True), (MAX, True), (MAX + 1, False)])
def test_UM08_nickname_length_boundary(
    signed_in: TestClient, repo: FakeRepo, length: int, ok: bool
) -> None:
    """AC-boundary: max - 1 and max pass, max + 1 is refused (code points after trimming)."""
    response = patch_nickname(signed_in, "ก" * length)

    if ok:
        assert response.status_code == 200, response.text
        assert repo.updates == [{"nickname": "ก" * length}]
    else:
        assert_error(response, 422, "validation_error")
        assert repo.updates == []


def test_UM08_nickname_cap_counts_code_points_not_graphemes(
    signed_in: TestClient, repo: FakeRepo
) -> None:
    """AC-boundary (decision 2, like PersonaText): "กี" is one grapheme but two code points,
    so max code points pass and one more is refused."""
    at_cap = ("กี" * MAX)[:MAX]

    assert patch_nickname(signed_in, at_cap).status_code == 200
    assert_error(patch_nickname(signed_in, at_cap + "ก"), 422, "validation_error")


def test_UM08_spaces_around_do_not_use_up_the_cap(signed_in: TestClient, repo: FakeRepo) -> None:
    """AC-boundary: too long before trimming, within the cap after."""
    response = patch_nickname(signed_in, "  " + "ก" * MAX + "  ")

    assert response.status_code == 200, response.text
    assert repo.updates == [{"nickname": "ก" * MAX}]


# --- the shape of the body (AC-7, AC-7b) --------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        {"nickname": "ปาล์ม", "education_level": "university"},
        {"explain_language": "en"},
        {"auto_read": True},
        {"setup_step": "done"},
        {"foo": 1},
        {"nickname": 5},
        {"nickname": True},
        ["ปาล์ม"],
        {},
    ],
    ids=[
        "education_level",
        "explain_language",
        "auto_read",
        "setup_step",
        "unknown",
        "number",
        "boolean",
        "array",
        "empty-object",
    ],
)
def test_UM09_patch_body_outside_the_contract_is_422(
    signed_in: TestClient, repo: FakeRepo, body: Any
) -> None:
    """AC-7 and AC-7b: other fields, wrong types, not an object, or `{}`. Nothing saved."""
    assert_error(signed_in.patch(PATH, json=body), 422, "validation_error")
    assert repo.updates == []
