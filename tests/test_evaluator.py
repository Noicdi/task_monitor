from pathlib import Path

from task_monitor.evaluator import (
    EXIT_FAILED,
    EXIT_LOG_ERROR_SUCCESS,
    EXIT_START_ERROR,
    EXIT_SUCCESS,
    EXIT_TIMEOUT,
    evaluate,
)
from task_monitor.models import JobConfig, ProcessResult, StructuredLogResult


def job(notify_on_success=False):
    return JobConfig("daily", Path("/tmp/job.py"), "python3", 1, notify_on_success)


def process(exit_code=0, timed_out=False, started=True):
    return ProcessResult(started=started, pid=123 if started else None, exit_code=exit_code, timed_out=timed_out)


def slog(valid=True, status="success", error=None):
    return StructuredLogResult(
        found=True,
        valid=valid,
        status=status if valid else None,
        message="msg" if valid else None,
        error_message=error,
        raw_line=None,
        line_count=1,
        expected_number=1,
        line_count_sufficient=True,
    )


def test_timeout_wins():
    result = evaluate(job(), process(exit_code=None, timed_out=True), slog(valid=True))

    assert result.final_status == "timeout"
    assert result.exit_code == EXIT_TIMEOUT
    assert result.should_notify is True


def test_success_uses_notify_on_success():
    result = evaluate(job(notify_on_success=False), process(0), slog(True, "success"))

    assert result.final_status == "success"
    assert result.exit_code == EXIT_SUCCESS
    assert result.should_notify is False


def test_failed_structured_log_status_fails():
    result = evaluate(job(), process(0), slog(True, "failed"))

    assert result.final_status == "failed"
    assert result.exit_code == EXIT_FAILED
    assert result.should_notify is True


def test_log_error_with_zero_exit_is_success_with_log_error():
    result = evaluate(job(), process(0), slog(False, error="line count too low"))

    assert result.final_status == "success_with_log_error"
    assert result.exit_code == EXIT_LOG_ERROR_SUCCESS
    assert result.should_notify is True


def test_log_error_with_non_zero_exit_fails():
    result = evaluate(job(), process(2), slog(False, error="bad json"))

    assert result.final_status == "failed"
    assert result.exit_code == EXIT_FAILED


def test_start_failure_returns_start_error():
    result = evaluate(job(), process(None, started=False), slog(False, error="missing"))

    assert result.final_status == "failed"
    assert result.exit_code == EXIT_START_ERROR

