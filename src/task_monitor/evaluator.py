from .models import EvaluationResult, JobConfig, ProcessResult, StructuredLogResult


EXIT_SUCCESS = 0
EXIT_FAILED = 1
EXIT_TIMEOUT = 2
EXIT_CONFIG_ERROR = 3
EXIT_CACHE_ERROR = 4
EXIT_START_ERROR = 5
EXIT_LOG_ERROR_SUCCESS = 6
EXIT_NOTIFY_FAILED = 7
EXIT_INTERNAL_ERROR = 10


def evaluate(
    job_config: JobConfig,
    process_result: ProcessResult,
    structured_log_result: StructuredLogResult,
) -> EvaluationResult:
    if process_result.timed_out:
        return EvaluationResult(
            final_status="timeout",
            should_notify=True,
            exit_code=EXIT_TIMEOUT,
            title="Task timed out: {}".format(job_config.name),
            message=process_result.error_message or "task timed out",
        )

    if not process_result.started:
        return EvaluationResult(
            final_status="failed",
            should_notify=True,
            exit_code=EXIT_START_ERROR,
            title="Task start failed: {}".format(job_config.name),
            message=process_result.error_message or "task failed to start",
        )

    if structured_log_result.valid:
        if structured_log_result.status == "success":
            return EvaluationResult(
                final_status="success",
                should_notify=job_config.notify_on_success,
                exit_code=EXIT_SUCCESS,
                title="Task succeeded: {}".format(job_config.name),
                message=structured_log_result.message or "",
            )
        return EvaluationResult(
            final_status="failed",
            should_notify=True,
            exit_code=EXIT_FAILED,
            title="Task failed: {}".format(job_config.name),
            message=structured_log_result.message or "",
        )

    exit_code = process_result.exit_code
    if exit_code == 0:
        return EvaluationResult(
            final_status="success_with_log_error",
            should_notify=True,
            exit_code=EXIT_LOG_ERROR_SUCCESS,
            title="Task succeeded with structured log error: {}".format(job_config.name),
            message=structured_log_result.error_message or "structured log error",
        )

    return EvaluationResult(
        final_status="failed",
        should_notify=True,
        exit_code=EXIT_FAILED,
        title="Task failed: {}".format(job_config.name),
        message=structured_log_result.error_message or "structured log error",
    )

