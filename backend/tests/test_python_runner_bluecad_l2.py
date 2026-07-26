import pytest

from app.modules.runner.safety import RunnerSafetyError, preflight_bluecad_l2_ast_policy


@pytest.mark.parametrize(
    "module",
    ["os", "sys", "subprocess", "socket", "requests", "httpx", "urllib", "importlib"],
)
def test_bluecad_l2_lint_rejects_disallowed_imports(module: str) -> None:
    with pytest.raises(RunnerSafetyError) as exc_info:
        preflight_bluecad_l2_ast_policy(f"import {module}\n")
    assert exc_info.value.code == "SANDBOX_VIOLATION"


@pytest.mark.parametrize(
    "source",
    [
        "from . import x\n",
        "from math import *\n",
        "eval('1')\n",
        "exec('x=1')\n",
        "__import__('os')\n",
        "builtins.eval('1')\n",
        "builtins.exec('x=1')\n",
        "builtins.__import__('os')\n",
        "f = eval\nf('1')\n",
        "f = eval\nmod = f(\"__import__('o'+'s')\")\nmod.listdir('.')\n",
        "g = getattr\ng(x, 'y')\n",
    ],
)
def test_bluecad_l2_lint_rejects_dynamic_or_unknown_import_forms(source: str) -> None:
    with pytest.raises(RunnerSafetyError) as exc_info:
        preflight_bluecad_l2_ast_policy(source)
    assert exc_info.value.code == "SANDBOX_VIOLATION"


def test_bluecad_l2_lint_allows_reviewed_build123d_and_stdlib_source() -> None:
    preflight_bluecad_l2_ast_policy(
        """
import build123d
import json
import math
from pathlib import Path

output_dir = Path(".")
payload = {"ok": math.sqrt(4)}
(output_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
""".strip()
    )


@pytest.mark.parametrize(
    "module",
    [
        "build123d",
        "collections",
        "collections.abc",
        "dataclasses",
        "decimal",
        "enum",
        "functools",
        "itertools",
        "json",
        "math",
        "operator",
        "pathlib",
        "statistics",
        "typing",
    ],
)
def test_bluecad_l2_lint_allows_explicit_import_roots(module: str) -> None:
    preflight_bluecad_l2_ast_policy(f"import {module}\n")
    preflight_bluecad_l2_ast_policy(f"from {module} import placeholder\n")
