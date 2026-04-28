from datetime import datetime
from pathlib import Path

from .cache import CacheError, next_execution_number
from .config import ConfigError, get_job, load_config
from .context import build_context
from .evaluator import (
    EXIT_CACHE_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_INTERNAL_ERROR,
    EXIT_NOTIFY_FAILED,
    evaluate,
)
from .models import EvaluationResult, ProcessResult, StructuredLogResult
from .monitor_logger import setup_logger, setup_stderr_logger
from .notifier import build_notification_text, send_feishu_text
from .runner import run_job
from .structured_log import read_structured_log


def run(config_path: Path, job_name: str) -> int:
    date = datetime.now().strftime("%Y%m%d")
    logger = setup_stderr_logger()

    try:
        app_config = load_config(config_path)
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        return EXIT_CONFIG_ERROR

    logger = setup_logger(app_config.global_config.monitor_log_dir, date)
    logger.info("task monitor started config=%s job=%s", config_path, job_name)

    try:
        job_config = get_job(app_config, job_name)
    except ConfigError as exc:
        evaluation = _monitor_error("Configuration error", str(exc), EXIT_CONFIG_ERROR)
        _notify_monitor_error(app_config.feishu.webhook, evaluation, logger)
        return EXIT_CONFIG_ERROR

    context = None
    process_result = None
    structured_log_result = None

    try:
        number = next_execution_number(app_config.global_config.cache_dir, date, job_name, logger)
        logger.info("execution number generated job=%s number=%s", job_name, number)

        context = build_context(config_path, app_config.global_config, job_config, date, number)
        logger.info(
            "run context built script=%s interpreter=%s timeout=%s structured_log=%s",
            job_config.script,
            job_config.interpreter,
            job_config.timeout_seconds,
            context.structured_log_path,
        )

        process_result = run_job(job_config)
        logger.info(
            "process result started=%s pid=%s exit_code=%s timed_out=%s error=%s",
            process_result.started,
            process_result.pid,
            process_result.exit_code,
            process_result.timed_out,
            process_result.error_message,
        )

        if process_result.timed_out:
            structured_log_result = _skipped_structured_log(context.number)
        else:
            structured_log_result = read_structured_log(context.structured_log_path, context.number)
            logger.info(
                "structured log result found=%s valid=%s line_count=%s expected=%s sufficient=%s error=%s",
                structured_log_result.found,
                structured_log_result.valid,
                structured_log_result.line_count,
                structured_log_result.expected_number,
                structured_log_result.line_count_sufficient,
                structured_log_result.error_message,
            )

        evaluation = evaluate(job_config, process_result, structured_log_result)
        logger.info(
            "evaluation result status=%s should_notify=%s exit_code=%s message=%s",
            evaluation.final_status,
            evaluation.should_notify,
            evaluation.exit_code,
            evaluation.message,
        )

        if evaluation.should_notify:
            text = build_notification_text(context, evaluation, process_result, structured_log_result)
            notification = send_feishu_text(app_config.feishu.webhook, text)
            if not notification.success:
                logger.error(
                    "notification failed original_status=%s original_exit_code=%s error=%s",
                    evaluation.final_status,
                    evaluation.exit_code,
                    notification.error_message,
                )
                return EXIT_NOTIFY_FAILED
            logger.info("notification sent")

        logger.info("task monitor finished exit_code=%s", evaluation.exit_code)
        return evaluation.exit_code
    except CacheError as exc:
        evaluation = _monitor_error("Cache error", str(exc), EXIT_CACHE_ERROR)
        logger.error("cache error: %s", exc)
        if _notify_monitor_error(app_config.feishu.webhook, evaluation, logger):
            return EXIT_CACHE_ERROR
        return EXIT_NOTIFY_FAILED
    except Exception as exc:  # pragma: no cover - defensive boundary
        evaluation = _monitor_error("Internal error", str(exc), EXIT_INTERNAL_ERROR)
        logger.exception("unexpected internal error")
        if _notify_monitor_error(app_config.feishu.webhook, evaluation, logger):
            return EXIT_INTERNAL_ERROR
        return EXIT_NOTIFY_FAILED


def _monitor_error(title: str, message: str, exit_code: int) -> EvaluationResult:
    return EvaluationResult(
        final_status="monitor_error",
        should_notify=True,
        exit_code=exit_code,
        title=title,
        message=message,
    )


def _notify_monitor_error(webhook: str, evaluation: EvaluationResult, logger) -> bool:
    notification = send_feishu_text(webhook, build_notification_text(None, evaluation))
    if not notification.success:
        logger.error("monitor error notification failed: %s", notification.error_message)
        return False
    logger.info("monitor error notification sent")
    return True


def _skipped_structured_log(expected_number: int) -> StructuredLogResult:
    return StructuredLogResult(
        found=False,
        valid=False,
        status=None,
        message=None,
        error_message="structured log skipped because task timed out",
        raw_line=None,
        line_count=0,
        expected_number=expected_number,
        line_count_sufficient=False,
    )

