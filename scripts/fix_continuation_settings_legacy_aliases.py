from __future__ import annotations

from pathlib import Path

PATH = Path("backend/app/modules/ai/models.py")
OLD = '''    scaleway_live_smoke_test_enabled: bool | None = None
    scaleway_monthly_token_cap: int | None = Field(default=None, ge=0)
'''
NEW = '''    scaleway_live_smoke_test_enabled: bool | None = None
    # Recognized legacy write-only aliases. The settings service intentionally ignores them.
    scaleway_token_cap: int | None = Field(default=None, ge=0)
    scaleway_tokens_month_to_date: int | None = Field(default=None, ge=0)
    scaleway_monthly_token_cap: int | None = Field(default=None, ge=0)
'''

source = PATH.read_text(encoding="utf-8")
if source.count(OLD) != 1:
    raise RuntimeError("legacy settings alias insertion point is missing or ambiguous")
PATH.write_text(source.replace(OLD, NEW), encoding="utf-8")
