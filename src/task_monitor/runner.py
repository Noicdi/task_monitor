import shlex
import subprocess

from .models import JobConfig, ProcessResult


def run_job(job_config: JobConfig) -> ProcessResult:
    if not job_config.script.exists():
        return ProcessResult(
            started=False,
            pid=None,
            exit_code=None,
            timed_out=False,
            error_message="script does not exist: {}".format(job_config.script),
        )
    if not job_config.script.is_file():
        return ProcessResult(
            started=False,
            pid=None,
            exit_code=None,
            timed_out=False,
            error_message="script path is not a file: {}".format(job_config.script),
        )

    try:
        args = shlex.split(job_config.interpreter) + [str(job_config.script)]
    except ValueError as exc:
        return ProcessResult(
            started=False,
            pid=None,
            exit_code=None,
            timed_out=False,
            error_message="invalid interpreter command: {}".format(exc),
        )

    try:
        process = subprocess.Popen(args)
    except OSError as exc:
        return ProcessResult(
            started=False,
            pid=None,
            exit_code=None,
            timed_out=False,
            error_message="failed to start process: {}".format(exc),
        )

    try:
        exit_code = process.wait(timeout=job_config.timeout_seconds)
        return ProcessResult(
            started=True,
            pid=process.pid,
            exit_code=exit_code,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        return ProcessResult(
            started=True,
            pid=process.pid,
            exit_code=None,
            timed_out=True,
            error_message="process timed out after {} seconds".format(job_config.timeout_seconds),
        )

