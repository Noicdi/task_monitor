import json
import logging
import os
import tempfile
from pathlib import Path

import fcntl


class CacheError(Exception):
    pass


def next_execution_number(cache_dir: Path, date: str, job_name: str, logger=None) -> int:
    logger = logger or logging.getLogger(__name__)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CacheError("failed to create cache directory: {}".format(exc)) from exc

    cache_path = cache_dir / "execution_numbers.json"
    lock_path = cache_dir / "execution_numbers.lock"

    try:
        with lock_path.open("a+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            data = _read_cache(cache_path, logger)
            if data.get("date") != date:
                data = {"date": date, "jobs": {}}
            jobs = data.setdefault("jobs", {})
            if not isinstance(jobs, dict):
                logger.warning("cache jobs section is invalid; rebuilding cache")
                data = {"date": date, "jobs": {}}
                jobs = data["jobs"]
            current = jobs.get(job_name, 0)
            if not isinstance(current, int) or isinstance(current, bool) or current < 0:
                logger.warning("cache value for job %s is invalid; resetting it", job_name)
                current = 0
            number = current + 1
            jobs[job_name] = number
            _write_cache(cache_path, data)
            return number
    except OSError as exc:
        raise CacheError("failed to update cache: {}".format(exc)) from exc


def _read_cache(cache_path: Path, logger) -> dict:
    if not cache_path.exists():
        return {"date": "", "jobs": {}}
    try:
        with cache_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cache file is damaged; rebuilding cache: %s", exc)
        return {"date": "", "jobs": {}}
    if not isinstance(data, dict):
        logger.warning("cache root is invalid; rebuilding cache")
        return {"date": "", "jobs": {}}
    return data


def _write_cache(cache_path: Path, data: dict) -> None:
    fd, tmp_name = tempfile.mkstemp(
        prefix="execution_numbers.",
        suffix=".tmp",
        dir=str(cache_path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, cache_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

