from pathlib import Path
from typing import Any, Dict

from .models import AppConfig, FeishuConfig, GlobalConfig, JobConfig

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    import tomli as tomllib  # type: ignore


class ConfigError(Exception):
    pass


def load_config(path: Path) -> AppConfig:
    try:
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError("config file does not exist: {}".format(path)) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError("invalid TOML config: {}".format(exc)) from exc
    except OSError as exc:
        raise ConfigError("failed to read config: {}".format(exc)) from exc

    if not isinstance(raw, dict):
        raise ConfigError("config root must be a table")

    global_section = _required_table(raw, "global")
    feishu_section = _required_table(raw, "feishu")
    jobs_section = _required_table(raw, "jobs")

    global_config = GlobalConfig(
        structured_log_root=Path(_required_str(global_section, "structured_log_root")),
        cache_dir=Path(_required_str(global_section, "cache_dir")),
        monitor_log_dir=Path(_required_str(global_section, "monitor_log_dir")),
    )
    feishu = FeishuConfig(webhook=_required_str(feishu_section, "webhook"))

    jobs = {}
    for name, value in jobs_section.items():
        if not isinstance(value, dict):
            raise ConfigError("jobs.{} must be a table".format(name))
        jobs[name] = JobConfig(
            name=name,
            script=Path(_required_str(value, "script")),
            interpreter=_required_str(value, "interpreter"),
            timeout_seconds=_required_positive_int(value, "timeout_seconds"),
            notify_on_success=_required_bool(value, "notify_on_success"),
        )

    if not jobs:
        raise ConfigError("jobs must contain at least one job")

    return AppConfig(global_config=global_config, feishu=feishu, jobs=jobs)


def get_job(config: AppConfig, job_name: str) -> JobConfig:
    try:
        return config.jobs[job_name]
    except KeyError as exc:
        raise ConfigError("job does not exist: {}".format(job_name)) from exc


def _required_table(raw: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError("{} must be a table".format(key))
    return value


def _required_str(raw: Dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError("{} must be a non-empty string".format(key))
    return value


def _required_positive_int(raw: Dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError("{} must be a positive integer".format(key))
    return value


def _required_bool(raw: Dict[str, Any], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ConfigError("{} must be a boolean".format(key))
    return value

