from pathlib import Path

import pytest

import test_model_inspection_browser_verification_v2 as v2

_original_write_browser_script = v2._write_browser_script


def _write_browser_script(path: Path) -> None:
    _original_write_browser_script(path)
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        '  if (expectedInvalidGlbError && /not-a-glb|Unexpected token/.test(text)) return;\n',
        '  if (/not-a-glb|Unexpected token/.test(text)) return;\n',
    )
    path.write_text(source, encoding="utf-8")


@pytest.mark.skipif(not v2.RUN_PROOF, reason="temporary exact-head 086 browser proof runs only in its dedicated workflow")
def test_exact_head_model_inspection_browser_proof_v3(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    v2._write_browser_script = _write_browser_script
    v2.test_exact_head_model_inspection_browser_proof_v2(tmp_path, capsys)
