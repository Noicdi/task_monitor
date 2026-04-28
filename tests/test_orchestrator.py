import sys
from datetime import datetime

from task_monitor import orchestrator
from task_monitor.evaluator import EXIT_LOG_ERROR_SUCCESS, EXIT_NOTIFY_FAILED, EXIT_SUCCESS
from task_monitor.models import NotificationResult


def write_config(path, root, cache, logs, script, notify_on_success=False):
    path.write_text(
        """
[global]
structured_log_root = "{root}"
cache_dir = "{cache}"
monitor_log_dir = "{logs}"

[feishu]
webhook = "https://example.invalid/hook"

[jobs.daily]
script = "{script}"
interpreter = "{interpreter}"
timeout_seconds = 5
notify_on_success = {notify}
""".format(
            root=root,
            cache=cache,
            logs=logs,
            script=script,
            interpreter=sys.executable,
            notify=str(notify_on_success).lower(),
        ),
        encoding="utf-8",
    )


def test_orchestrator_success_without_notification(tmp_path, monkeypatch):
    date = datetime.now().strftime("%Y%m%d")
    structured_root = tmp_path / "structured"
    log_dir = structured_root / date
    log_dir.mkdir(parents=True)
    script = tmp_path / "job.py"
    script.write_text(
        "from pathlib import Path\n"
        "p = Path({!r}) / {!r} / 'daily.log'\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "with p.open('a', encoding='utf-8') as f:\n"
        "    f.write('{{\"status\":\"success\",\"message\":\"ok\"}}\\n')\n".format(str(structured_root), date),
        encoding="utf-8",
    )
    config = tmp_path / "config.toml"
    write_config(config, structured_root, tmp_path / "cache", tmp_path / "logs", script)

    called = []
    monkeypatch.setattr(orchestrator, "send_feishu_text", lambda *args, **kwargs: called.append(args))

    assert orchestrator.run(config, "daily") == EXIT_SUCCESS
    assert called == []


def test_orchestrator_log_line_shortage_notifies(tmp_path, monkeypatch):
    script = tmp_path / "job.py"
    script.write_text("pass\n", encoding="utf-8")
    config = tmp_path / "config.toml"
    write_config(config, tmp_path / "structured", tmp_path / "cache", tmp_path / "logs", script)

    notifications = []

    def fake_notify(*args, **kwargs):
        notifications.append(args)
        return NotificationResult(True)

    monkeypatch.setattr(orchestrator, "send_feishu_text", fake_notify)

    assert orchestrator.run(config, "daily") == EXIT_LOG_ERROR_SUCCESS
    assert len(notifications) == 1


def test_orchestrator_notification_failure_returns_7(tmp_path, monkeypatch):
    date = datetime.now().strftime("%Y%m%d")
    structured_root = tmp_path / "structured"
    script = tmp_path / "job.py"
    script.write_text(
        "from pathlib import Path\n"
        "p = Path({!r}) / {!r} / 'daily.log'\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "with p.open('a', encoding='utf-8') as f:\n"
        "    f.write('{{\"status\":\"success\",\"message\":\"ok\"}}\\n')\n".format(str(structured_root), date),
        encoding="utf-8",
    )
    config = tmp_path / "config.toml"
    write_config(config, structured_root, tmp_path / "cache", tmp_path / "logs", script, True)

    monkeypatch.setattr(
        orchestrator,
        "send_feishu_text",
        lambda *args, **kwargs: NotificationResult(False, "network"),
    )

    assert orchestrator.run(config, "daily") == EXIT_NOTIFY_FAILED
