"""AI-04: the app's own loggers reach stderr at LOG_LEVEL as JSON lines (self-review of PR #95).

Uvicorn configures only its own loggers, so without app.main's setup the INFO line of every AI
call (logger ``app.ai.calls``, specs/features/ai/ai-calls-log.md §2.3) would be dropped on
Cloud Run.
"""

import json
import logging

import pytest

import app.main as main_module


@pytest.fixture
def app_logger():
    logger = logging.getLogger("app")
    handlers, level = list(logger.handlers), logger.level
    logger.handlers.clear()
    yield logger
    logger.handlers[:] = handlers
    logger.setLevel(level)


def test_AI04_app_loggers_write_json_lines_at_log_level(app_logger, capsys):
    main_module._configure_logging("info")

    logging.getLogger("app.ai.calls").info('{"purpose": "tutor_reply"}')
    logging.getLogger("app.ai.calls").debug("hidden below LOG_LEVEL")

    lines = [line for line in capsys.readouterr().err.splitlines() if line]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["severity"] == "INFO"
    assert entry["logger"] == "app.ai.calls"
    assert json.loads(entry["message"]) == {"purpose": "tutor_reply"}


def test_AI04_logging_setup_does_not_add_a_second_handler(app_logger):
    main_module._configure_logging("info")
    main_module._configure_logging("warning")

    assert len(app_logger.handlers) == 1
    assert app_logger.level == logging.WARNING
