from pathlib import Path

import pytest

from task_monitor.config import ConfigError, get_job, load_config


def write_config(path: Path, extra: str = "") -> None:
    path.write_text(
        """
[global]
structured_log_root = "/tmp/structured"
cache_dir = "/tmp/cache"
monitor_log_dir = "/tmp/logs"

[feishu]
webhook = "https://example.invalid/hook"

[jobs.daily_sync]
script = "/tmp/job.py"
interpreter = "python3"
timeout_seconds = 10
notify_on_success = false
{}
""".format(extra),
        encoding="utf-8",
    )


def test_load_config_success(tmp_path):
    path = tmp_path / "config.toml"
    write_config(path)

    config = load_config(path)

    assert config.global_config.structured_log_root == Path("/tmp/structured")
    assert get_job(config, "daily_sync").timeout_seconds == 10


def test_missing_config_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.toml")


def test_invalid_timeout_raises_config_error(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
[global]
structured_log_root = "/tmp/structured"
cache_dir = "/tmp/cache"
monitor_log_dir = "/tmp/logs"

[feishu]
webhook = "https://example.invalid/hook"

[jobs.daily_sync]
script = "/tmp/job.py"
interpreter = "python3"
timeout_seconds = 0
notify_on_success = false
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(path)


def test_get_missing_job_raises_config_error(tmp_path):
    path = tmp_path / "config.toml"
    write_config(path)
    config = load_config(path)

    with pytest.raises(ConfigError):
        get_job(config, "missing")

