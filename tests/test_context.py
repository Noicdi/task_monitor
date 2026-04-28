from pathlib import Path

from task_monitor.context import build_context
from task_monitor.models import GlobalConfig, JobConfig


def test_structured_log_path_uses_job_file_without_number():
    global_config = GlobalConfig(
        structured_log_root=Path("/data/logs"),
        cache_dir=Path("/cache"),
        monitor_log_dir=Path("/monitor"),
    )
    job_config = JobConfig(
        name="daily_sync",
        script=Path("/opt/job.py"),
        interpreter="python3",
        timeout_seconds=10,
        notify_on_success=False,
    )

    context = build_context(Path("/etc/config.toml"), global_config, job_config, "20260428", 3)

    assert context.structured_log_path == Path("/data/logs/20260428/daily_sync.log")
    assert context.number == 3

