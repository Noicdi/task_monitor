from pathlib import Path

from .models import GlobalConfig, JobConfig, RunContext


def build_context(
    config_path: Path,
    global_config: GlobalConfig,
    job_config: JobConfig,
    date: str,
    number: int,
) -> RunContext:
    structured_log_path = global_config.structured_log_root / date / "{}.jsonl".format(job_config.name)
    return RunContext(
        job_name=job_config.name,
        date=date,
        number=number,
        structured_log_path=structured_log_path,
        config_path=config_path,
        job_config=job_config,
        global_config=global_config,
    )

