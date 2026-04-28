import json

from task_monitor.cache import next_execution_number


def test_same_day_same_job_increments(tmp_path):
    assert next_execution_number(tmp_path, "20260428", "daily") == 1
    assert next_execution_number(tmp_path, "20260428", "daily") == 2


def test_different_jobs_count_separately(tmp_path):
    assert next_execution_number(tmp_path, "20260428", "daily") == 1
    assert next_execution_number(tmp_path, "20260428", "report") == 1


def test_date_change_resets_counts(tmp_path):
    assert next_execution_number(tmp_path, "20260428", "daily") == 1
    assert next_execution_number(tmp_path, "20260429", "daily") == 1


def test_damaged_cache_is_rebuilt(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "execution_numbers.json").write_text("{bad json", encoding="utf-8")

    assert next_execution_number(tmp_path, "20260428", "daily") == 1
    data = json.loads((tmp_path / "execution_numbers.json").read_text(encoding="utf-8"))
    assert data["jobs"]["daily"] == 1

