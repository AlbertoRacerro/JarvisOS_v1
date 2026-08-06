import base64
import hashlib
from pathlib import Path

import pytest


def test_generate_exact_083_reconciliation_blob(capsys: pytest.CaptureFixture[str]) -> None:
    root = Path(__file__).resolve().parents[2]
    status_path = root / "docs" / "specs" / "STATUS.md"
    source = status_path.read_text(encoding="utf-8")

    old_priority = "3. Spec 070 UI-FOUNDATION-1 remains merged and reconciled; spec 083 APP-SHELL-1 is `in_review` in implementation [PR #231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231). The Penpot visual-identity work remains a separate independently removable lane."
    new_priority = "3. Specs 070 UI-FOUNDATION-1 and 083 APP-SHELL-1 are merged and reconciled; spec 084 BLUECAD-READ-MODEL-1 remains the next planned frontend-beta slice. The Penpot visual-identity work remains a separate independently removable lane."

    old_row = "| 083 | in_review | [#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231) | APP-SHELL-1 | 006, 070 | Implementation PR #231 implements only the identity-independent shell under [the 2026-08-05 readiness decision](083-readiness-2026-08-05.md) and the [complete APP-SHELL-1 specification](083-app-shell-1.md), including the bounded [UI-foundation checker reconciliation](083-ui-foundation-checker-amendment-2026-08-05.md) and [production SPA fallback](083-spa-fallback-amendment-2026-08-05.md); Penpot visual identity remains separate and independently removable. |"
    new_row = "| 083 | merged | [#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231) | APP-SHELL-1 | 006, 070 | PR #231 merged the identity-independent shell under [the 2026-08-05 readiness decision](083-readiness-2026-08-05.md) and the [complete APP-SHELL-1 specification](083-app-shell-1.md), including the bounded [UI-foundation checker reconciliation](083-ui-foundation-checker-amendment-2026-08-05.md) and [production SPA fallback](083-spa-fallback-amendment-2026-08-05.md); Penpot visual identity remains separate and independently removable. |"

    assert source.count(old_priority) == 1
    assert source.count(old_row) == 1
    assert source.count(new_priority) == 0
    assert source.count(new_row) == 0

    result = source.replace(old_priority, new_priority).replace(old_row, new_row)
    assert result.count(new_priority) == 1
    assert result.count(new_row) == 1
    assert "| 084 | planned | — | BLUECAD-READ-MODEL-1 |" in result

    encoded = base64.b64encode(result.encode("utf-8")).decode("ascii")
    digest = hashlib.sha256(result.encode("utf-8")).hexdigest()
    with capsys.disabled():
        print(f"RECONCILE_083_BYTES={len(result.encode('utf-8'))}", flush=True)
        print(f"RECONCILE_083_SHA256={digest}", flush=True)
        print(f"RECONCILE_083_BASE64={encoded}", flush=True)
