from pathlib import Path

from task_monitor.models import (
    EvaluationResult,
    GlobalConfig,
    JobConfig,
    ProcessResult,
    RunContext,
    StructuredLogResult,
)
from task_monitor.notifier import build_notification_text


def test_notification_text_contains_structured_log_line_metadata():
    job = JobConfig("daily", Path("/opt/job.py"), "python3", 10, False)
    context = RunContext(
        job_name="daily",
        date="20260428",
        number=3,
        structured_log_path=Path("/logs/20260428/daily.jsonl"),
        config_path=Path("/etc/task_monitor/config.toml"),
        job_config=job,
        global_config=GlobalConfig(Path("/logs"), Path("/cache"), Path("/monitor")),
    )
    evaluation = EvaluationResult("success", True, 0, "ok", "finished")
    process = ProcessResult(True, 123, 0, False)
    structured = StructuredLogResult(
        found=True,
        valid=True,
        status="success",
        message="finished",
        error_message=None,
        raw_line=None,
        line_count=3,
        expected_number=3,
        line_count_sufficient=True,
    )

    text = build_notification_text(context, evaluation, process, structured)

    assert "编号: 3" in text
    assert "结构化日志路径: /logs/20260428/daily.jsonl" in text
    assert "结构化日志行数: 3" in text
    assert "日志行数满足编号: True" in text

