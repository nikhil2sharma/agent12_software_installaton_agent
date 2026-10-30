import csv

import pytest

from version_agent import cli
from version_agent.checker import NOT_FOUND


def write_csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_read_rows_skips_blank_names(tmp_path):
    f = write_csv(tmp_path / "in.csv", "name,version\nfastapi,0.110.0\n,\n")
    assert [r["name"] for r in cli.read_rows(f)] == ["fastapi"]


def test_read_rows_requires_name_column(tmp_path):
    f = write_csv(tmp_path / "in.csv", "tool,version\nfastapi,1\n")
    with pytest.raises(ValueError):
        cli.read_rows(f)


def test_check_all_and_write(tmp_path, monkeypatch):
    latest = {"fastapi": "0.120.0", "python": "3.11.4", "mystery": NOT_FOUND}
    monkeypatch.setattr(cli, "find_latest_version", lambda c, name, url, model: latest[name])

    rows = [
        {"name": "fastapi", "version": "0.110.0", "url": ""},
        {"name": "python", "version": "3.11.4", "url": ""},
        {"name": "mystery", "version": "", "url": ""},
    ]
    out = tmp_path / "out.csv"
    cli.write_rows(out, cli.check_all(None, rows, "model"))

    with out.open(encoding="utf-8") as f:
        status = {r["name"]: r["status"] for r in csv.DictReader(f)}
    assert status == {"fastapi": "OUTDATED", "python": "UP_TO_DATE", "mystery": "UNKNOWN"}


def test_main_missing_file_returns_1(tmp_path):
    assert cli.main([str(tmp_path / "nope.csv")]) == 1
