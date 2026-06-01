import json
import logging

from delivery_route_api.logging import JsonLogFormatter, get_log_level


def test_get_log_level_returns_valid_level() -> None:
    assert get_log_level("debug") == logging.DEBUG
    assert get_log_level("INFO") == logging.INFO
    assert get_log_level("invalid") == logging.INFO


def test_json_log_formatter_outputs_structured_log() -> None:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="test_message",
        args=(),
        exc_info=None,
    )

    formatted = JsonLogFormatter().format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "test_message"
    assert "timestamp" in payload
    assert "module" in payload
    assert "function" in payload
    assert "line" in payload