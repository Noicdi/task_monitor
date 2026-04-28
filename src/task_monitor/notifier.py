import json
import socket
from datetime import datetime
from typing import Optional
from urllib import error, request

from .models import EvaluationResult, NotificationResult, ProcessResult, RunContext, StructuredLogResult


def build_notification_text(
    context: Optional[RunContext],
    evaluation: EvaluationResult,
    process_result: Optional[ProcessResult] = None,
    structured_log_result: Optional[StructuredLogResult] = None,
) -> str:
    lines = [
        "任务: {}".format(context.job_name if context else "-"),
        "日期: {}".format(context.date if context else "-"),
        "编号: {}".format(context.number if context else "-"),
        "最终状态: {}".format(evaluation.final_status),
        "消息: {}".format(evaluation.message),
        "业务脚本退出码: {}".format(_format_value(process_result.exit_code if process_result else None)),
        "是否超时: {}".format(process_result.timed_out if process_result else False),
        "结构化日志路径: {}".format(context.structured_log_path if context else "-"),
        "结构化日志行数: {}".format(
            _format_value(structured_log_result.line_count if structured_log_result else None)
        ),
        "日志行数满足编号: {}".format(
            structured_log_result.line_count_sufficient if structured_log_result else "-"
        ),
        "业务脚本路径: {}".format(context.job_config.script if context else "-"),
        "主机名: {}".format(socket.gethostname()),
        "发生时间: {}".format(datetime.now().isoformat(timespec="seconds")),
    ]
    return "\n".join(lines)


def send_feishu_text(webhook: str, text: str, timeout: int = 10) -> NotificationResult:
    payload = json.dumps(
        {
            "msg_type": "text",
            "content": {"text": text},
        }
    ).encode("utf-8")
    req = request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            if resp.status >= 400:
                return NotificationResult(False, "Feishu HTTP status {}".format(resp.status))
            try:
                data = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return NotificationResult(True)
            code = data.get("code")
            if code not in (None, 0):
                return NotificationResult(False, "Feishu response code {}: {}".format(code, data))
            return NotificationResult(True)
    except (OSError, error.URLError, error.HTTPError) as exc:
        return NotificationResult(False, str(exc))


def _format_value(value) -> str:
    return "-" if value is None else str(value)

