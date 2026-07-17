from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT = Path(__file__).with_name("apply_token_flow_local_wiring.py")
OLD = '    (ROOT / ".github/workflows/ci.yml").write_bytes(_decode(CI_B64))'
NEW = (
    '    template = ROOT / "scripts/token_flow_ci_clean.yml"\n'
    '    (ROOT / ".github/workflows/ci.yml").write_bytes(template.read_bytes())\n'
    '    template.unlink()'
)


def main() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    if source.count(OLD) != 1:
        raise RuntimeError("clean workflow replacement point is not unique")
    SCRIPT.write_text(source.replace(OLD, NEW), encoding="utf-8")
    runpy.run_path(str(SCRIPT), run_name="__main__")
    Path(__file__).unlink()


if __name__ == "__main__":
    main()
