#!/usr/bin/env python3
"""Verify JarvisOS merge-authority policy against deterministic or live GitHub state.

This verifier is read-only. It never mutates repository settings and never grants
merge authority. Overall precedence is ERROR > MISMATCH > UNKNOWN > VERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

POLICY_PATH = Path(".github/merge-authority-policy.json")
SCHEMA = "jarvisos.merge-authority.v1"
STATES = ("VERIFIED", "MISMATCH", "UNKNOWN", "ERROR")
STATE_RANK = {"VERIFIED": 0, "UNKNOWN": 1, "MISMATCH": 2, "ERROR": 3}
POLICY_KEYS = {
    "schema_version",
    "repository",
    "branch",
    "require_protection",
    "require_status_checks",
    "required_check_contexts",
    "allow_auto_merge",
    "normal_merge_owner_bypass",
    "merge_methods",
}


class PolicyError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def policy_digest(policy: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(policy).encode("utf-8")).hexdigest()


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot load policy: {exc}") from exc
    if not isinstance(raw, dict):
        raise PolicyError("policy must be a JSON object")
    unknown = set(raw) - POLICY_KEYS
    missing = POLICY_KEYS - set(raw)
    if unknown or missing:
        raise PolicyError(f"policy keys mismatch: missing={sorted(missing)} unknown={sorted(unknown)}")
    if raw["schema_version"] != SCHEMA:
        raise PolicyError(f"unsupported schema_version: {raw['schema_version']!r}")
    if raw["repository"] != "AlbertoRacerro/JarvisOS_v1" or raw["branch"] != "master":
        raise PolicyError("policy target must be AlbertoRacerro/JarvisOS_v1/master")
    if raw["require_protection"] is not True or raw["require_status_checks"] is not True:
        raise PolicyError("V1 requires protection and status checks")
    contexts = raw["required_check_contexts"]
    if not isinstance(contexts, list) or not contexts or any(not isinstance(v, str) or not v.strip() for v in contexts):
        raise PolicyError("required_check_contexts must be a non-empty string list")
    if len(set(contexts)) != len(contexts):
        raise PolicyError("required_check_contexts contains duplicates")
    if raw["allow_auto_merge"] is not False:
        raise PolicyError("V1 cannot authorize deferred auto-merge")
    if raw["normal_merge_owner_bypass"] != "forbidden":
        raise PolicyError("V1 normal merge-owner bypass must be forbidden")
    if raw["merge_methods"] != "observe_only":
        raise PolicyError("V1 merge methods must remain observe_only")
    return raw


def finding(control: str, state: str, reason: str) -> dict[str, str]:
    if state not in STATES:
        raise ValueError(state)
    return {"control": control, "state": state, "reason": reason}


def _error_status(value: Any) -> int | None:
    if isinstance(value, dict) and isinstance(value.get("_error_status"), int):
        return value["_error_status"]
    return None


def _required_contexts_from_branch(branch: dict[str, Any]) -> tuple[set[str] | None, str]:
    protection = branch.get("protection")
    if not isinstance(protection, dict):
        return None, "branch protection summary unavailable"
    status = protection.get("required_status_checks")
    if not isinstance(status, dict):
        return None, "required status-check summary unavailable"
    contexts: set[str] = set()
    raw_contexts = status.get("contexts", [])
    raw_checks = status.get("checks", [])
    if isinstance(raw_contexts, list):
        contexts.update(v for v in raw_contexts if isinstance(v, str))
    if isinstance(raw_checks, list):
        for item in raw_checks:
            if isinstance(item, dict) and isinstance(item.get("context"), str):
                contexts.add(item["context"])
    enforcement = status.get("enforcement_level")
    if enforcement == "off":
        return contexts, "required status-check enforcement is off"
    return contexts, "required status-check summary readable"


def classify(policy: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if not isinstance(snapshot, dict):
        findings.append(finding("snapshot", "ERROR", "snapshot must be an object"))
        return _report(policy, snapshot if isinstance(snapshot, dict) else {}, findings)

    repo = snapshot.get("repository")
    branch = snapshot.get("branch")
    rulesets = snapshot.get("rulesets")
    detailed = snapshot.get("detailed_protection")

    if not isinstance(repo, dict):
        findings.append(finding("repository", "ERROR", "repository metadata missing or malformed"))
    else:
        full_name = repo.get("full_name")
        if full_name != policy["repository"]:
            findings.append(finding("target.repository", "ERROR", f"wrong repository: {full_name!r}"))
        else:
            findings.append(finding("target.repository", "VERIFIED", full_name))
        auto_merge = repo.get("allow_auto_merge")
        if auto_merge is None:
            findings.append(finding("auto_merge", "UNKNOWN", "allow_auto_merge is unreadable"))
        elif bool(auto_merge) != policy["allow_auto_merge"]:
            findings.append(finding("auto_merge", "MISMATCH", f"allow_auto_merge={auto_merge!r}"))
        else:
            findings.append(finding("auto_merge", "VERIFIED", "deferred auto-merge is disabled"))

    protected: bool | None = None
    if not isinstance(branch, dict):
        findings.append(finding("branch", "ERROR", "branch metadata missing or malformed"))
    else:
        branch_name = branch.get("name")
        if branch_name != policy["branch"]:
            findings.append(finding("target.branch", "ERROR", f"wrong branch: {branch_name!r}"))
        else:
            findings.append(finding("target.branch", "VERIFIED", branch_name))
        raw_protected = branch.get("protected")
        if isinstance(raw_protected, bool):
            protected = raw_protected
            if policy["require_protection"] and not protected:
                findings.append(finding("protection", "MISMATCH", "branch reports protected=false"))
            elif protected:
                findings.append(finding("protection", "VERIFIED", "branch reports protected=true"))
        else:
            findings.append(finding("protection", "UNKNOWN", "branch protected flag unreadable"))

        contexts, context_reason = _required_contexts_from_branch(branch)
        required = set(policy["required_check_contexts"])
        if protected is False:
            findings.append(finding("required_status_checks", "MISMATCH", context_reason))
        elif contexts is None:
            findings.append(finding("required_status_checks", "UNKNOWN", context_reason))
        else:
            missing = sorted(required - contexts)
            if missing:
                findings.append(finding("required_status_checks", "MISMATCH", f"missing required contexts: {missing}"))
            else:
                findings.append(finding("required_status_checks", "VERIFIED", f"required contexts present: {sorted(required)}"))

    if isinstance(rulesets, list):
        findings.append(finding("rulesets.visibility", "VERIFIED", f"readable ruleset count={len(rulesets)}"))
    elif _error_status(rulesets):
        findings.append(finding("rulesets.visibility", "UNKNOWN", f"rulesets endpoint HTTP {_error_status(rulesets)}"))
    else:
        findings.append(finding("rulesets.visibility", "UNKNOWN", "rulesets response unavailable"))

    detail_error = _error_status(detailed)
    if isinstance(detailed, dict) and detail_error is None:
        enforce_admins = detailed.get("enforce_admins")
        enabled = enforce_admins.get("enabled") if isinstance(enforce_admins, dict) else None
        if enabled is True:
            findings.append(finding("normal_merge_owner_bypass", "VERIFIED", "classic protection enforce_admins=true"))
        elif enabled is False:
            findings.append(finding("normal_merge_owner_bypass", "MISMATCH", "classic protection enforce_admins=false"))
        else:
            findings.append(finding("normal_merge_owner_bypass", "UNKNOWN", "admin enforcement detail unreadable"))
    elif protected is False:
        findings.append(finding("normal_merge_owner_bypass", "MISMATCH", "unprotected branch cannot enforce normal-owner gates"))
    elif detail_error:
        findings.append(finding("normal_merge_owner_bypass", "UNKNOWN", f"detailed protection HTTP {detail_error}"))
    else:
        findings.append(finding("normal_merge_owner_bypass", "UNKNOWN", "detailed protection unavailable"))

    merge_methods = snapshot.get("merge_methods")
    if isinstance(merge_methods, dict):
        enabled = sorted(k for k, v in merge_methods.items() if v is True)
        findings.append(finding("merge_methods", "VERIFIED", f"observe_only enabled={enabled}"))
    else:
        findings.append(finding("merge_methods", "UNKNOWN", "merge-method metadata unavailable"))

    return _report(policy, snapshot, findings)


def _report(policy: dict[str, Any], snapshot: dict[str, Any], findings: list[dict[str, str]]) -> dict[str, Any]:
    overall = max((item["state"] for item in findings), key=lambda state: STATE_RANK[state], default="ERROR")
    branch = snapshot.get("branch") if isinstance(snapshot, dict) else None
    commit = branch.get("commit") if isinstance(branch, dict) else None
    sha = commit.get("sha") if isinstance(commit, dict) and isinstance(commit.get("sha"), str) else None
    return {
        "schema_version": SCHEMA,
        "repository": policy["repository"],
        "branch": policy["branch"],
        "policy_digest": policy_digest(policy),
        "observed_sha": sha,
        "state": overall,
        "findings": findings,
    }


def _request_json(url: str, token: str | None) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "jarvisos-merge-authority-verifier"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"_error_status": exc.code}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {"_error_status": 599, "_error_type": type(exc).__name__}


def live_snapshot(policy: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    repo = policy["repository"]
    branch = policy["branch"]
    base = f"https://api.github.com/repos/{repo}"
    repo_data = _request_json(base, token)
    branch_data = _request_json(f"{base}/branches/{branch}", token)
    rulesets = _request_json(f"{base}/rulesets", token)
    detailed = _request_json(f"{base}/branches/{branch}/protection", token)
    merge_methods: dict[str, bool] | None = None
    if isinstance(repo_data, dict) and _error_status(repo_data) is None:
        merge_methods = {
            "merge_commit": repo_data.get("allow_merge_commit") is True,
            "squash": repo_data.get("allow_squash_merge") is True,
            "rebase": repo_data.get("allow_rebase_merge") is True,
        }
    return {
        "repository": repo_data,
        "branch": branch_data,
        "rulesets": rulesets,
        "detailed_protection": detailed,
        "merge_methods": merge_methods,
    }


def _self_test_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "repository": "AlbertoRacerro/JarvisOS_v1",
        "branch": "master",
        "require_protection": True,
        "require_status_checks": True,
        "required_check_contexts": ["backend", "evidence"],
        "allow_auto_merge": False,
        "normal_merge_owner_bypass": "forbidden",
        "merge_methods": "observe_only",
    }


def _base_snapshot(*, protected: bool = True, auto_merge: bool = False) -> dict[str, Any]:
    return {
        "repository": {"full_name": "AlbertoRacerro/JarvisOS_v1", "allow_auto_merge": auto_merge},
        "branch": {
            "name": "master",
            "protected": protected,
            "commit": {"sha": "a" * 40},
            "protection": {
                "enabled": protected,
                "required_status_checks": {
                    "enforcement_level": "non_admins" if protected else "off",
                    "contexts": ["backend", "evidence"] if protected else [],
                    "checks": [],
                },
            },
        },
        "rulesets": [],
        "detailed_protection": {"enforce_admins": {"enabled": True}} if protected else {"_error_status": 403},
        "merge_methods": {"merge_commit": True, "squash": True, "rebase": True},
    }


def self_test() -> None:
    policy = _self_test_policy()
    assert classify(policy, _base_snapshot())["state"] == "VERIFIED"

    current = _base_snapshot(protected=False)
    assert classify(policy, current)["state"] == "MISMATCH"

    unknown = _base_snapshot()
    unknown["branch"]["protection"] = {"enabled": True}
    unknown["detailed_protection"] = {"_error_status": 403}
    assert classify(policy, unknown)["state"] == "UNKNOWN"

    auto = _base_snapshot(auto_merge=True)
    assert classify(policy, auto)["state"] == "MISMATCH"

    wrong = _base_snapshot()
    wrong["repository"]["full_name"] = "other/repo"
    assert classify(policy, wrong)["state"] == "ERROR"

    mixed = _base_snapshot(protected=False)
    mixed["rulesets"] = {"_error_status": 403}
    assert classify(policy, mixed)["state"] == "MISMATCH", "MISMATCH must outrank UNKNOWN"

    malformed = _base_snapshot()
    malformed["repository"] = None
    assert classify(policy, malformed)["state"] == "ERROR", "ERROR must outrank all"

    assert policy_digest(policy) == policy_digest(json.loads(canonical_json(policy)))
    assert "Authorization" not in canonical_json(classify(policy, _base_snapshot()))

    bad = dict(policy)
    bad["allow_auto_merge"] = True
    try:
        path = Path(os.environ.get("RUNNER_TEMP", ".")) / "merge-authority-self-test-policy.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        load_policy(path)
    except PolicyError:
        pass
    else:
        raise AssertionError("auto-merge policy must be rejected")
    finally:
        try:
            path.unlink()
        except (OSError, UnboundLocalError):
            pass

    print("merge-authority verifier self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        if not args.snapshot and not args.live:
            return 0

    try:
        policy = load_policy(args.policy)
    except PolicyError as exc:
        print(f"merge-authority policy ERROR: {exc}", file=sys.stderr)
        return 4

    if args.snapshot and args.live:
        parser.error("choose only one of --snapshot or --live")
    if args.snapshot:
        try:
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"snapshot ERROR: {exc}", file=sys.stderr)
            return 4
    elif args.live:
        snapshot = live_snapshot(policy, os.environ.get("GITHUB_TOKEN"))
    else:
        parser.error("one of --snapshot, --live, or --self-test is required")

    report = classify(policy, snapshot)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"merge-authority {report['state']} repo={report['repository']} branch={report['branch']} policy={report['policy_digest'][:12]}")
        for item in report["findings"]:
            print(f"- {item['state']:8s} {item['control']}: {item['reason']}")

    return {"VERIFIED": 0, "MISMATCH": 2, "UNKNOWN": 3, "ERROR": 4}[report["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
