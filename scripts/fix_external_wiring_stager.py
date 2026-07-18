from __future__ import annotations

from pathlib import Path

PATH = Path("scripts/apply_token_flow_external_wiring.py")

OLD = '''    source = replace_exact(
        source,
        """    ledger_id = _terminal_job(
        task_kind=task_kind,
""",
        """    ledger_id = _terminal_job(
        flow_id=flow_id,
        task_kind=task_kind,
""",
        expected=2,
    )
'''
NEW = '''    source = replace_exact(
        source,
        """    ledger_id = _terminal_job(
        task_kind=task_kind,
""",
        """    ledger_id = _terminal_job(
        flow_id=flow_id,
        task_kind=task_kind,
""",
        expected=1,
    )
    source = replace_exact(
        source,
        """        ledger_id = _terminal_job(
            task_kind=task_kind,
""",
        """        ledger_id = _terminal_job(
            flow_id=flow_id,
            task_kind=task_kind,
""",
        expected=1,
    )
'''

source = PATH.read_text(encoding="utf-8")
if source.count(OLD) != 1:
    raise RuntimeError("external wiring stager target is missing or ambiguous")
PATH.write_text(source.replace(OLD, NEW), encoding="utf-8")
