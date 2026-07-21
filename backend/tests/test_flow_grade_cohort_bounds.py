from __future__ import annotations

import pytest

from app.modules.ai.flow_grade_cohort_store import load_cohort_rows
from app.modules.ai.flow_grade_contracts import FlowGradeContractError


def test_cohort_limit_is_bounded() -> None:
    with pytest.raises(ValueError, match="between 1 and 5000"):
        load_cohort_rows(workspace_id=None, task_kind=None, limit=0)
    with pytest.raises(ValueError, match="between 1 and 5000"):
        load_cohort_rows(workspace_id=None, task_kind=None, limit=5001)


def test_cohort_filter_identifiers_fail_closed() -> None:
    with pytest.raises(FlowGradeContractError, match="workspace_id is invalid"):
        load_cohort_rows(workspace_id="bad id", task_kind=None, limit=10)
    with pytest.raises(FlowGradeContractError, match="task_kind is invalid"):
        load_cohort_rows(workspace_id=None, task_kind="bad id", limit=10)
