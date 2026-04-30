# task-monitor

Lightweight Linux cron task monitor for Python business scripts.

The monitor runs one configured job per invocation, starts the business script, evaluates the appended JSON Lines structured log, and sends Feishu notifications according to the result.

## Usage

```bash
task_monitor --config /etc/task_monitor/config.toml --job daily_sync
```

## Structured Log

Business scripts append one JSON object per run to:

```text
${structured_log_root}/${date}/${job}.jsonl
```

Example:

```json
{"status":"success","message":"finished"}
```

The monitor compares its cached execution number with the file line count. If the execution number is greater than the line count, the structured log is treated as missing for this run.

