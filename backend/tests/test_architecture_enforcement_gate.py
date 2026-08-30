from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_architecture_enforcement.py"


def _write_config(root: Path, exceptions: list[dict[str, str]] | None = None) -> Path:
    path = root / "configs" / "architecture_enforcement.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"exceptions": exceptions or []}), encoding="utf-8")
    return path


def _run(root: Path, config: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--root", str(root)]
    if config is not None:
        command += ["--config", str(config)]
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _exception(rule_id: str, exact_match: str, owner: str = "test-owner") -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "exact_match": exact_match,
        "classification": "accepted_test_fixture",
        "owner_or_removal_spec": owner,
        "rationale": "focused deterministic fixture",
    }


def test_self_test() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


def test_ae001_accepts_exact_owner_and_rejects_aliased_connection(tmp_path: Path) -> None:
    owner = tmp_path / "backend/app/core/database.py"
    owner.parent.mkdir(parents=True)
    owner.write_text(
        "import sqlite3\n\ndef open_sqlite_connection():\n    return sqlite3.connect('ok')\n",
        encoding="utf-8",
    )
    bad = tmp_path / "backend/app/feature.py"
    bad.write_text(
        "import sqlite3 as db\n\ndef open_other():\n    return db.connect('bad')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE001", "backend/app/core/database.py::open_sqlite_connection", "core database boundary")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE001 backend/app/feature.py::open_other" in result.stdout
    assert "database.py::open_sqlite_connection" not in result.stdout


def test_ae001_exact_exception_does_not_cover_sibling_symbol(tmp_path: Path) -> None:
    source = tmp_path / "scripts/data_root_recovery/snapshot.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "import sqlite3\n"
        "def create_snapshot():\n    return sqlite3.connect('accepted')\n"
        "def unexpected_snapshot_owner():\n    return sqlite3.connect('bad')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE001", "scripts/data_root_recovery/snapshot.py::create_snapshot", "021b")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE001 scripts/data_root_recovery/snapshot.py::unexpected_snapshot_owner" in result.stdout
    assert "snapshot.py::create_snapshot" not in result.stdout


def test_ae002_preserves_exact_debt_and_rejects_new_dispatch(tmp_path: Path) -> None:
    debt = tmp_path / "backend/app/modules/ai/deepseek_provider_smoke.py"
    debt.parent.mkdir(parents=True)
    debt.write_text(
        "from app.modules.ai.providers.deepseek import DeepSeekProviderAdapter\n"
        "def run_provider_smoke(a):\n    return a.complete('x')\n",
        encoding="utf-8",
    )
    bad = tmp_path / "backend/app/new_network.py"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        "import httpx as h\n\ndef send():\n    return h.post('https://example.invalid')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE002", "backend/app/modules/ai/deepseek_provider_smoke.py::run_provider_smoke", "129")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE002 backend/app/new_network.py::send" in result.stdout
    assert "deepseek_provider_smoke.py::run_provider_smoke" not in result.stdout


def test_ae002_exact_exception_does_not_cover_sibling_symbol(tmp_path: Path) -> None:
    source = tmp_path / "backend/app/modules/ai/execution.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from app.modules.ai.providers.deepseek import DeepSeekProviderAdapter\n"
        "def run_ai_task(adapter):\n    return adapter.complete('accepted')\n"
        "def bypass(adapter):\n    return adapter.complete('bad')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE002", "backend/app/modules/ai/execution.py::run_ai_task", "059b")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE002 backend/app/modules/ai/execution.py::bypass" in result.stdout
    assert "execution.py::run_ai_task" not in result.stdout


def test_ae003_preserves_exact_debt_and_rejects_new_canonical_sql(tmp_path: Path) -> None:
    debt = tmp_path / "backend/app/modules/modeling/service.py"
    debt.parent.mkdir(parents=True)
    debt.write_text(
        "def create_model_spec(c):\n    c.execute('INSERT INTO model_specs (id) VALUES (?)')\n",
        encoding="utf-8",
    )
    bad = tmp_path / "backend/app/modules/other/service.py"
    bad.parent.mkdir(parents=True)
    bad.write_text(
        "def mutate(c):\n    c.execute('UPDATE requirements SET statement = ?')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE003", "backend/app/modules/modeling/service.py::create_model_spec", "127")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE003 backend/app/modules/other/service.py::mutate" in result.stdout
    assert "modeling/service.py::create_model_spec" not in result.stdout


def test_ae003_exact_exception_does_not_cover_sibling_symbol(tmp_path: Path) -> None:
    source = tmp_path / "backend/app/modules/runner/service.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "def create_runner_job(c):\n    c.execute('INSERT INTO simulation_runs (id) VALUES (?)')\n"
        "def unexpected_owner(c):\n    c.execute('UPDATE simulation_runs SET status = ?')\n",
        encoding="utf-8",
    )
    config = _write_config(
        tmp_path,
        [_exception("AE003", "backend/app/modules/runner/service.py::create_runner_job", "runner lifecycle")],
    )
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE003 backend/app/modules/runner/service.py::unexpected_owner" in result.stdout
    assert "runner/service.py::create_runner_job" not in result.stdout


def test_ae003_ignores_sql_looking_text_passed_to_non_sql_call(tmp_path: Path) -> None:
    source = tmp_path / "scripts/check_architecture_enforcement.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from pathlib import Path\n"
        "def _self_test(path: Path):\n"
        "    path.write_text(\"c.execute('UPDATE requirements SET statement = ?')\")\n",
        encoding="utf-8",
    )
    config = _write_config(tmp_path)
    result = _run(tmp_path, config)
    assert result.returncode == 0, result.stdout + result.stderr


def test_ae004_inert_text_passes_but_issue_comment_mutator_fails(tmp_path: Path) -> None:
    script = tmp_path / "scripts/note.py"
    script.parent.mkdir(parents=True)
    script.write_text("TEXT='JARVIS_COORD_V2 WORKPACK only'\n", encoding="utf-8")
    workflow = tmp_path / ".github/workflows/apply.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: apply\non:\n  issue_comment:\njobs: {}\n", encoding="utf-8")
    config = _write_config(tmp_path)
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert "AE004 .github/workflows/apply.yml::on.issue_comment" in result.stdout
    assert "scripts/note.py" not in result.stdout


def test_config_fails_closed_on_wildcard_unknown_duplicate_and_stale_target(tmp_path: Path) -> None:
    target = tmp_path / "backend/app/x.py"
    target.parent.mkdir(parents=True)
    target.write_text("def f():\n    pass\n", encoding="utf-8")
    cases = [
        [_exception("AE001", "backend/app/*::f")],
        [_exception("AE999", "backend/app/x.py::f")],
        [_exception("AE001", "backend/app/x.py::f"), _exception("AE001", "backend/app/x.py::f")],
        [_exception("AE001", "backend/app/x.py::missing")],
    ]
    for entries in cases:
        result = _run(tmp_path, _write_config(tmp_path, entries))
        assert result.returncode == 2
        assert "ARCH_CONFIG_ERROR" in result.stderr


def test_diagnostics_are_stable(tmp_path: Path) -> None:
    source = tmp_path / "backend/app/x.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "import sqlite3 as s\nimport httpx as h\ndef z():\n"
        "    s.connect('x')\n    h.get('https://example.invalid')\n",
        encoding="utf-8",
    )
    config = _write_config(tmp_path)
    first = _run(tmp_path, config)
    second = _run(tmp_path, config)
    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout
