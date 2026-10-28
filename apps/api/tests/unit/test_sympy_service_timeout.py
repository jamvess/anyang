"""SymPy worker pool: real worker processes, timeout and restart.

Spec: specs/features/check/sympy-service.md §2.5 (AC-23, AC-24, AC-29, AC-boundary). One pool is
shared by the module because starting a worker (Python + SymPy import) takes about 2 seconds.
"""

import time

import pytest

from app.math.sympy_service import (
    SympyTimeoutError,
    SympyWorkerPool,
    check_lines,
    default_pool,
)
from app.settings import get_settings

# Test inputs, not learning thresholds: a short timeout so the hang test is quick, and the time
# allowed on top of it for killing the worker.
SHORT_TIMEOUT_S = 0.5
KILL_MARGIN_S = 5.0
# Long enough for a warm worker to answer; the first call may also wait for the worker to start.
GENEROUS_TIMEOUT_S = 30.0


@pytest.fixture(scope="module")
def pool():
    pool = SympyWorkerPool(workers=1)
    yield pool
    pool.close()


async def test_AM04_job_within_timeout_returns_its_value(pool: SympyWorkerPool) -> None:
    # AC-boundary: finishes before the timeout -> not timed out.
    assert await pool.run(abs, -3, timeout_s=GENEROUS_TIMEOUT_S) == 3


async def test_AM04_hanging_job_times_out_and_returns_quickly(pool: SympyWorkerPool) -> None:
    # AC-23 + AC-boundary: a job longer than the timeout is stopped.
    await pool.run(abs, 0, timeout_s=GENEROUS_TIMEOUT_S)  # make sure the worker is warm
    started = time.monotonic()

    with pytest.raises(SympyTimeoutError):
        await pool.run(time.sleep, 60, timeout_s=SHORT_TIMEOUT_S)

    assert time.monotonic() - started < SHORT_TIMEOUT_S + KILL_MARGIN_S


async def test_AM04_pool_works_again_after_a_timeout(pool: SympyWorkerPool) -> None:
    # AC-24: the killed worker is replaced; the next real check is correct.
    with pytest.raises(SympyTimeoutError):
        await pool.run(time.sleep, 60, timeout_s=SHORT_TIMEOUT_S)

    result = await check_lines(
        answer_format="factored",
        reference_answer="x(x-1)(x+1)",
        lines=["x^{3}-x", "=x(x^{2}-1)"],
        timeout_s=GENEROUS_TIMEOUT_S,
        pool=pool,
    )

    assert result.timed_out is False
    assert result.final_equal is True
    assert result.final_in_form is False
    assert result.line_ok == [True, True]


def test_AM04_default_pool_size_comes_from_config() -> None:
    # AC-29
    assert default_pool().workers == get_settings().learning.checker.sympy_workers


def test_AM04_default_pool_is_shared() -> None:
    # §2.5: warm workers are reused, not started per request.
    assert default_pool() is default_pool()
