from task_monitor.structured_log import read_structured_log


def test_missing_file_is_invalid(tmp_path):
    result = read_structured_log(tmp_path / "daily.jsonl", 1)

    assert result.valid is False
    assert result.found is False
    assert result.line_count == 0


def test_reads_last_line_when_line_count_is_sufficient(tmp_path):
    path = tmp_path / "daily.jsonl"
    path.write_text(
        '{"status":"failed","message":"first"}\n{"status":"success","message":"last"}\n',
        encoding="utf-8",
    )

    result = read_structured_log(path, 2)

    assert result.valid is True
    assert result.status == "success"
    assert result.message == "last"
    assert result.line_count == 2
    assert result.line_count_sufficient is True


def test_number_greater_than_line_count_is_invalid(tmp_path):
    path = tmp_path / "daily.jsonl"
    path.write_text('{"status":"success","message":"first"}\n', encoding="utf-8")

    result = read_structured_log(path, 2)

    assert result.valid is False
    assert result.line_count == 1
    assert result.line_count_sufficient is False


def test_message_non_string_is_converted(tmp_path):
    path = tmp_path / "daily.jsonl"
    path.write_text('{"status":"success","message":123}\n', encoding="utf-8")

    result = read_structured_log(path, 1)

    assert result.valid is True
    assert result.message == "123"


def test_invalid_status_is_invalid(tmp_path):
    path = tmp_path / "daily.jsonl"
    path.write_text('{"status":"unknown","message":"x"}\n', encoding="utf-8")

    result = read_structured_log(path, 1)

    assert result.valid is False

