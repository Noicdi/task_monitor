import os
import signal
import sys
import time

from task_monitor.models import JobConfig
from task_monitor.runner import run_job


def test_runner_supports_interpreter_arguments(tmp_path):
    script = tmp_path / "job.py"
    output = tmp_path / "out.txt"
    script.write_text(
        "from pathlib import Path\nPath({!r}).write_text('ok', encoding='utf-8')\n".format(str(output)),
        encoding="utf-8",
    )
    result = run_job(JobConfig("daily", script, "{} -u".format(sys.executable), 5, False))

    assert result.started is True
    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8") == "ok"


def test_runner_missing_script_fails(tmp_path):
    result = run_job(JobConfig("daily", tmp_path / "missing.py", sys.executable, 1, False))

    assert result.started is False
    assert "does not exist" in result.error_message


def test_timeout_does_not_kill_process(tmp_path):
    script = tmp_path / "sleep.py"
    script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    result = run_job(JobConfig("daily", script, sys.executable, 1, False))

    assert result.started is True
    assert result.timed_out is True
    os.kill(result.pid, 0)
    os.kill(result.pid, signal.SIGTERM)
    time.sleep(0.1)

