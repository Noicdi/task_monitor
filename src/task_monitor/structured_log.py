import json
from pathlib import Path

from .models import StructuredLogResult


def read_structured_log(path: Path, expected_number: int) -> StructuredLogResult:
    if not path.exists():
        return _invalid(False, 0, expected_number, "structured log does not exist: {}".format(path))
    if not path.is_file():
        return _invalid(True, 0, expected_number, "structured log path is not a file: {}".format(path))

    try:
        with path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        return _invalid(True, 0, expected_number, "failed to read structured log: {}".format(exc))

    line_count = len(lines)
    if line_count == 0:
        return _invalid(True, line_count, expected_number, "structured log is empty")
    if expected_number > line_count:
        return _invalid(
            True,
            line_count,
            expected_number,
            "structured log line count {} is less than execution number {}".format(
                line_count, expected_number
            ),
        )

    raw_line = lines[-1].strip()
    if not raw_line:
        return _invalid(True, line_count, expected_number, "last structured log line is empty", raw_line)

    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        return _invalid(True, line_count, expected_number, "invalid JSON: {}".format(exc), raw_line)

    if not isinstance(payload, dict):
        return _invalid(True, line_count, expected_number, "structured log line must be a JSON object", raw_line)

    status = payload.get("status")
    if status not in ("success", "failed"):
        return _invalid(True, line_count, expected_number, "status must be success or failed", raw_line)

    message = payload.get("message", "")
    if not isinstance(message, str):
        message = str(message)

    return StructuredLogResult(
        found=True,
        valid=True,
        status=status,
        message=message,
        error_message=None,
        raw_line=raw_line,
        line_count=line_count,
        expected_number=expected_number,
        line_count_sufficient=True,
    )


def _invalid(
    found: bool,
    line_count: int,
    expected_number: int,
    error_message: str,
    raw_line: str = None,
) -> StructuredLogResult:
    return StructuredLogResult(
        found=found,
        valid=False,
        status=None,
        message=None,
        error_message=error_message,
        raw_line=raw_line,
        line_count=line_count,
        expected_number=expected_number,
        line_count_sufficient=line_count >= expected_number,
    )

