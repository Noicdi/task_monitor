from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class GlobalConfig:
    structured_log_root: Path
    cache_dir: Path
    monitor_log_dir: Path


@dataclass(frozen=True)
class FeishuConfig:
    webhook: str


@dataclass(frozen=True)
class JobConfig:
    name: str
    script: Path
    interpreter: str
    timeout_seconds: int
    notify_on_success: bool


@dataclass(frozen=True)
class AppConfig:
    global_config: GlobalConfig
    feishu: FeishuConfig
    jobs: dict


@dataclass(frozen=True)
class RunContext:
    job_name: str
    date: str
    number: int
    structured_log_path: Path
    config_path: Path
    job_config: JobConfig
    global_config: GlobalConfig


@dataclass(frozen=True)
class ProcessResult:
    started: bool
    pid: Optional[int]
    exit_code: Optional[int]
    timed_out: bool
    error_message: Optional[str] = None


@dataclass(frozen=True)
class StructuredLogResult:
    found: bool
    valid: bool
    status: Optional[str]
    message: Optional[str]
    error_message: Optional[str]
    raw_line: Optional[str]
    line_count: int
    expected_number: int
    line_count_sufficient: bool


@dataclass(frozen=True)
class EvaluationResult:
    final_status: str
    should_notify: bool
    exit_code: int
    title: str
    message: str


@dataclass(frozen=True)
class NotificationResult:
    success: bool
    error_message: Optional[str] = None

