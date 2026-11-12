from collections.abc import Iterator

import pytest

from tests.unit.network_guard import block_network, fail_if_attempted


@pytest.fixture(autouse=True)
def network_attempts() -> Iterator[list[str]]:
    """No unit test reaches the network, Supabase included (apps/api/CLAUDE.md). A local `.env`
    with SUPABASE_URL would otherwise send a test's fake token to the real anyang-dev. The guard
    test reads and clears the list it yields; any other test with an attempt fails."""
    with block_network() as attempts:
        yield attempts
    fail_if_attempted(attempts)
