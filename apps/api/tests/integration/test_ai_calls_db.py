"""AI-04: the Supabase writer inserts ai_calls rows with the service role (AC-17).

specs/features/ai/ai-calls-log.md §2 item 3.5. Runs against the local Supabase stack like
test_rls_isolation.py; the tenant is created here and deleted afterwards (rows cascade).
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from supabase import Client, ClientOptions, create_client

from app.ai.call_context import AICallContext
from app.ai.gateway import CallRecord
from app.db.ai_calls import SupabaseAICallsWriter, to_row
from app.settings import EnvSettings

_env = EnvSettings()
_URL = _env.supabase_url
_SERVICE_KEY = _env.supabase_service_role_key.get_secret_value()

if not (_URL and _SERVICE_KEY):
    if os.environ.get("CI"):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
    pytest.skip("Supabase is not configured", allow_module_level=True)

_NO_SESSION = {"auto_refresh_token": False, "persist_session": False}


@pytest.fixture(scope="module")
def admin() -> Client:
    return create_client(_URL, _SERVICE_KEY, ClientOptions(**_NO_SESSION))


@pytest.fixture
def tenant_id(admin: Client) -> Iterator[str]:
    tenant = admin.table("tenants").insert({"name": f"ai04-{uuid.uuid4().hex}"}).execute()
    tenant_id = tenant.data[0]["id"]
    try:
        yield tenant_id
    finally:
        admin.table("tenants").delete().eq("id", tenant_id).execute()


def _record(status: str, schema_retries: int) -> CallRecord:
    return CallRecord(
        purpose="extract_topics_local",
        provider="vertex",
        model="gemini-3.5-flash",
        prompt_version="v2",
        status=status,
        tokens_in=120,
        tokens_out=45,
        latency_ms=812.3,
        schema_retries=schema_retries,
    )


def test_AI04_service_role_inserts_ai_calls_row(admin: Client, tenant_id: str) -> None:
    writer = SupabaseAICallsWriter(_URL, _SERVICE_KEY)
    context = AICallContext(tenant_id=uuid.UUID(tenant_id))
    request_id = str(uuid.uuid4())
    # One row per status the mapping can give (ok, schema_retry, error), so the table's check
    # constraint is proven to accept all of them.
    records = [_record("ok", 0), _record("ok", 1), _record("schema_error", 2)]

    for call in records:
        writer.insert(to_row(call, context, request_id))

    stored = (
        admin.table("ai_calls")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("status")
        .execute()
        .data
    )
    assert [row["status"] for row in stored] == ["error", "ok", "schema_retry"]
    row = next(r for r in stored if r["status"] == "ok")
    expected = to_row(records[0], context, request_id)
    for column in ("purpose", "provider", "model", "prompt_version", "request_id"):
        assert row[column] == expected[column]
    assert row["tokens_in"] == 120
    assert row["tokens_out"] == 45
    assert row["latency_ms"] == 812
    assert row["user_id"] is None
    assert row["cost_usd"] is None
    assert row["fallback_used"] is False
