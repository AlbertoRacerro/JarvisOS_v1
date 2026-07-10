#!/usr/bin/env python3
"""Deterministic CI gate for ``docs/specs/STATUS.md``.

The gate validates the registry on every pull request. For an implementation PR
it also requires exactly one matching ``in_review`` row, the current PR number,
and only merged hard dependencies.

New PRs should declare one of these exact values in the PR body:

``**Spec gate:** implementation NNN``
``**Spec gate:** definition NNN``
``**Spec gate:** N/A``

For compatibility with already-open PRs, a row that already references the
current PR or a title containing ``Implement spec NNN`` is treated as an
implementation PR even when the field is absent.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REGISTRY_PATH = Path("docs/specs/STATUS.md")
ALLOWED_STATUSES = {
    "planned",
    "blocked",
    "ready",
    "in_progress",
    "in_review",
    "merged",
    "cancelled",
}
NO_ACTIVE_PR_STATUSES = {"planned", "blocked", "ready", "in_progress"}
DEFINITION_STATUSES = {"planned", "blocked", "ready"}
SPEC_ID_PATTERN = r"\d{3}[a-z]?"
SPEC_ID_RE = re.compile(rf"^{SPEC_ID_PATTERN}$", re.IGNORECASE)
PR_URL_RE = re.compile(r"/pull/(\d+)")
PR_HASH_RE = re.compile(r"(?<![\w/])#(\d+)\b")
DEPENDENCY_RE = re.compile(rf"\b({SPEC_ID_PATTERN})\b", re.IGNORECASE)
SPEC_GATE_RE = re.compile(
    rf"^\s*\*\*Spec gate:\*\*\s*"
    rf"(?:(implementation|definition)\s+({SPEC_ID_PATTERN})|(N/A))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TITLE_IMPLEMENTATION_RE = re.compile(
    rf"implement(?:ation of)?\s+spec\s+({SPEC_ID_PATTERN})\b",
    re.IGNORECASE,
)


class RegistryError(ValueError):
    """Raised when the registry or pull-request metadata violates the contract."""


@dataclass(frozen=True)
class SpecRow:
    spec_id: str
    status: str
    pr_cell: str
    name: str
    depends_on: str
    description: str

    @property
    def pr_numbers(self) -> tuple[int, ...]:
        numbers = {int(value) for value in PR_URL_RE.findall(self.pr_cell)}
        numbers.update(int(value) for value in PR_HASH_RE.findall(self.pr_cell))
        return tuple(sorted(numbers))

    @property
    def dependency_ids(self) -> tuple[str, ...]:
        if self.depends_on.strip() in {"", "-", "—"}:
            return ()
        return tuple(
            dict.fromkeys(
                match.lower() for match in DEPENDENCY_RE.findall(self.depends_on)
            )
        )


@dataclass(frozen=True)
class SpecGateDeclaration:
    mode: str
    spec_id: str | None = None


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_registry(text: str) -> dict[str, SpecRow]:
    rows: dict[str, SpecRow] = {}
    in_registry = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "## Registry":
            in_registry = True
            continue
        if in_registry and line.startswith("## "):
            break
        if not in_registry or not line.lstrip().startswith("|"):
            continue

        cells = _split_markdown_row(line)
        if not cells or cells[0] in {"Spec", "---"}:
            continue
        if len(cells) != 6:
            raise RegistryError(
                f"STATUS.md:{line_number}: expected 6 table columns, "
                f"found {len(cells)}"
            )

        spec_id, status, pr_cell, name, depends_on, description = cells
        normalized_id = spec_id.lower()
        if not SPEC_ID_RE.fullmatch(normalized_id):
            raise RegistryError(
                f"STATUS.md:{line_number}: invalid spec id {spec_id!r}"
            )
        if normalized_id in rows:
            raise RegistryError(
                f"STATUS.md:{line_number}: duplicate spec id {normalized_id}"
            )
        if status not in ALLOWED_STATUSES:
            raise RegistryError(
                f"STATUS.md:{line_number}: unsupported status {status!r} "
                f"for {normalized_id}"
            )

        row = SpecRow(
            spec_id=normalized_id,
            status=status,
            pr_cell=pr_cell,
            name=name,
            depends_on=depends_on,
            description=description,
        )
        if status in NO_ACTIVE_PR_STATUSES and row.pr_numbers:
            raise RegistryError(
                f"spec {normalized_id}: status {status!r} cannot carry an active "
                "implementation PR; use '—' until the implementation PR opens"
            )
        if status == "in_review" and not row.pr_numbers:
            raise RegistryError(
                f"spec {normalized_id}: in_review requires an implementation PR number"
            )
        rows[normalized_id] = row

    if not rows:
        raise RegistryError("STATUS.md: registry table is missing or empty")

    for row in rows.values():
        for dependency_id in row.dependency_ids:
            if dependency_id == row.spec_id:
                raise RegistryError(f"spec {row.spec_id}: cannot depend on itself")
            if dependency_id not in rows:
                raise RegistryError(
                    f"spec {row.spec_id}: dependency {dependency_id} "
                    "is absent from STATUS.md"
                )

    return rows


def parse_declaration(body: str) -> SpecGateDeclaration | None:
    matches = list(SPEC_GATE_RE.finditer(body))
    if len(matches) > 1:
        raise RegistryError("PR body contains more than one **Spec gate:** declaration")
    if not matches:
        return None

    match = matches[0]
    if match.group(3):
        return SpecGateDeclaration(mode="n/a")
    return SpecGateDeclaration(
        mode=match.group(1).lower(),
        spec_id=match.group(2).lower(),
    )


def _linked_rows(rows: dict[str, SpecRow], pr_number: int) -> list[SpecRow]:
    return [row for row in rows.values() if pr_number in row.pr_numbers]


def _validate_dependencies(row: SpecRow, rows: dict[str, SpecRow]) -> None:
    unmet = [
        f"{dependency_id}={rows[dependency_id].status}"
        for dependency_id in row.dependency_ids
        if rows[dependency_id].status != "merged"
    ]
    if unmet:
        raise RegistryError(
            f"spec {row.spec_id}: hard dependencies are not merged: "
            + ", ".join(unmet)
        )


def _validate_implementation(
    rows: dict[str, SpecRow],
    pr_number: int,
    spec_id: str,
) -> str:
    row = rows.get(spec_id)
    if row is None:
        raise RegistryError(
            f"PR #{pr_number}: implementation spec {spec_id} is absent from STATUS.md"
        )
    if row.status != "in_review":
        raise RegistryError(
            f"spec {spec_id}: implementation PR #{pr_number} requires status "
            f"'in_review', found {row.status!r}"
        )
    if pr_number not in row.pr_numbers:
        raise RegistryError(
            f"spec {spec_id}: STATUS.md does not reference current PR #{pr_number}"
        )
    _validate_dependencies(row, rows)
    return (
        f"spec-status: PR #{pr_number} -> implementation spec {spec_id}; "
        "status and dependencies valid"
    )


def _validate_definition(
    rows: dict[str, SpecRow],
    pr_number: int,
    spec_id: str,
) -> str:
    row = rows.get(spec_id)
    if row is None:
        raise RegistryError(
            f"PR #{pr_number}: definition spec {spec_id} is absent from STATUS.md"
        )
    if row.status not in DEFINITION_STATUSES:
        raise RegistryError(
            f"spec {spec_id}: definition PR requires one of "
            f"{sorted(DEFINITION_STATUSES)}, found {row.status!r}"
        )
    if pr_number in row.pr_numbers:
        raise RegistryError(
            f"spec {spec_id}: definition/planning PR #{pr_number} must not occupy "
            "the implementation PR column"
        )
    return f"spec-status: PR #{pr_number} -> definition spec {spec_id}; registry valid"


def validate_pull_request(
    rows: dict[str, SpecRow],
    event: dict[str, object],
) -> str:
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        return "spec-status: non-pull-request event; registry structure validated"

    raw_number = event.get("number")
    if not isinstance(raw_number, int):
        raise RegistryError("pull_request event is missing integer PR number")
    pr_number = raw_number
    body = str(pr.get("body") or "")
    title = str(pr.get("title") or "")
    declaration = parse_declaration(body)
    linked_rows = _linked_rows(rows, pr_number)

    if len(linked_rows) > 1:
        linked_ids = ", ".join(row.spec_id for row in linked_rows)
        raise RegistryError(
            f"PR #{pr_number}: referenced by multiple specs ({linked_ids}); "
            "one implementation PR may implement exactly one spec"
        )

    if declaration is not None:
        if declaration.mode == "n/a":
            if linked_rows:
                raise RegistryError(
                    f"PR #{pr_number}: declared N/A but STATUS.md assigns "
                    f"spec {linked_rows[0].spec_id}"
                )
            return f"spec-status: PR #{pr_number} declared N/A; registry valid"
        if declaration.spec_id is None:
            raise RegistryError("spec gate declaration is missing a spec id")
        if declaration.mode == "definition":
            return _validate_definition(rows, pr_number, declaration.spec_id)
        return _validate_implementation(rows, pr_number, declaration.spec_id)

    if linked_rows:
        return _validate_implementation(rows, pr_number, linked_rows[0].spec_id)

    title_match = TITLE_IMPLEMENTATION_RE.search(title)
    if title_match:
        return _validate_implementation(
            rows,
            pr_number,
            title_match.group(1).lower(),
        )

    return (
        f"spec-status: PR #{pr_number} has no spec-gate declaration; "
        "registry structure validated in compatibility mode"
    )


def load_event(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read GitHub event {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError(f"GitHub event {path} must contain a JSON object")
    return data


def run_check(registry_path: Path, event_path: Path | None) -> str:
    try:
        text = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegistryError(f"cannot read registry {registry_path}: {exc}") from exc
    rows = parse_registry(text)
    if event_path is None:
        return f"spec-status: registry valid ({len(rows)} rows)"
    return validate_pull_request(rows, load_event(event_path))


def _registry(*rows: str) -> str:
    body = "\n".join(rows)
    return (
        "# Spec status and roadmap\n\n"
        "## Registry\n\n"
        "| Spec | Status | PR | Name | Depends on | Description |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"{body}\n"
    )


def _event(
    number: int,
    *,
    declaration: str | None = "**Spec gate:** implementation 002",
    title: str = "Implement spec 002",
) -> dict[str, object]:
    return {
        "number": number,
        "pull_request": {
            "title": title,
            "body": declaration or "",
        },
    }


def _expect_failure(callable_obj: object, expected: str) -> None:
    try:
        callable_obj()  # type: ignore[operator]
    except RegistryError as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"expected failure containing {expected!r}")


def self_test() -> None:
    good = _registry(
        "| 001 | merged | [#10](https://example.test/pull/10) | Base | — | done |",
        "| 002 | in_review | [#99](https://example.test/pull/99) | Work | 001 | active |",
        "| 005b | ready | — | Suffixed | 001 | later |",
    )
    rows = parse_registry(good)
    assert validate_pull_request(rows, _event(99)).endswith(
        "status and dependencies valid"
    )
    assert "definition spec 005b" in validate_pull_request(
        rows,
        _event(
            77,
            declaration="**Spec gate:** definition 005b",
            title="Spec 005b definition",
        ),
    )
    assert "declared N/A" in validate_pull_request(
        rows,
        _event(77, declaration="**Spec gate:** N/A", title="Docs cleanup"),
    )

    _expect_failure(
        lambda: validate_pull_request(
            rows,
            _event(98, declaration="**Spec gate:** implementation 002"),
        ),
        "does not reference current PR",
    )

    wrong_status = _registry(
        "| 001 | merged | [#10](https://example.test/pull/10) | Base | — | done |",
        "| 002 | ready | [#99](https://example.test/pull/99) | Work | 001 | active |",
    )
    _expect_failure(
        lambda: parse_registry(wrong_status),
        "cannot carry an active implementation PR",
    )

    blocked_dependency = _registry(
        "| 001 | in_review | [#10](https://example.test/pull/10) | Base | — | active |",
        "| 002 | in_review | [#99](https://example.test/pull/99) | Work | 001 | active |",
    )
    _expect_failure(
        lambda: validate_pull_request(
            parse_registry(blocked_dependency),
            _event(99),
        ),
        "001=in_review",
    )

    assert rows["005b"].dependency_ids == ("001",)
    print("spec-status: self-test OK")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
        help="Path to docs/specs/STATUS.md",
    )
    parser.add_argument(
        "--event",
        type=Path,
        help="Path to the GitHub pull_request event JSON",
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            self_test()
            return 0
        print(run_check(args.registry, args.event))
        return 0
    except (RegistryError, AssertionError) as exc:
        print(f"spec-status: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
