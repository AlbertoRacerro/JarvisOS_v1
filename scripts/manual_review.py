#!/usr/bin/env python3
"""Run an explicitly requested advisory PR review without automatic actuation.

This wrapper reuses the hardened provider, prompt-pack, parsing, and GitHub helpers
from ``cheap_review.py``. It deliberately does not add or remove labels, trigger
another review tier, or mention Codex. A maintainer must dispatch the workflow and
must decide what to do with every finding.
"""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

from cheap_review import (
    AGENTS_SECTIONS,
    GITHUB_API,
    PROVIDER_ERRORS,
    build_prompt,
    call_model_with_retry,
    env,
    gh_request,
    list_pr_comments,
    next_round,
    parse_escalation,
    parse_verdict,
    post_comment,
    pr_head_sha,
    read_agents_sections,
    resolve_spec,
)

MANUAL_COMMENT_MARKER = "<!-- manual-review:{provider}:{tier} -->"


def _manual_prompt(prompt: str) -> str:
    sanitized = prompt.replace("@codex", "an implementation agent")
    return (
        "This review was explicitly requested by the maintainer. Return advisory "
        "findings only. Do not mention or address @codex, do not request an automated "
        "fix, do not apply or recommend workflow labels, and do not claim gate or merge "
        "authority. The maintainer will independently verify every finding.\n\n"
        + sanitized
    )


def _sanitize_review_output(review: str) -> str:
    """Prevent a disobedient reviewer from emitting an actionable Codex mention."""
    return review.replace("@codex", "Codex").replace("@Codex", "Codex")


def _fetch_pr(repo: str, pr_number: int, token: str) -> dict:
    status, payload = gh_request(
        "GET",
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}",
        token,
        accept="application/vnd.github+json",
    )
    if status != 200:
        raise RuntimeError(f"could not fetch PR #{pr_number} (status {status})")
    value = json.loads(payload)
    if not isinstance(value, dict) or "head" not in value:
        raise RuntimeError(f"GitHub returned an invalid PR payload for #{pr_number}")
    return value


def _manual_footer(*, approved: bool, escalation: str | None, stale_head: bool, truncated: bool) -> str:
    notes: list[str] = []
    if stale_head:
        notes.append(
            "A newer push landed while this review was running; the findings belong "
            "to a superseded head and must not be treated as current."
        )
    if truncated:
        notes.append("The diff exceeded the configured cap, so this review is partial.")
    if escalation:
        notes.append(
            f"The reviewer recommends an expert review: {escalation}. No expert "
            "workflow or label was triggered automatically."
        )
    elif approved:
        notes.append(
            "No blocking findings were reported. No readiness label was applied "
            "automatically; CI and the human maintainer remain the only merge authority."
        )
    else:
        notes.append(
            "Findings are advisory. No fix request was dispatched; the maintainer "
            "must verify them and may invoke an implementation agent manually."
        )
    return "\n\n" + "\n\n".join(f"_{note}_" for note in notes)


def self_test() -> None:
    prompt = _manual_prompt("base prompt with @codex reference")
    assert "explicitly requested" in prompt
    assert prompt.count("@codex") == 1
    assert "base prompt with an implementation agent reference" in prompt
    sanitized = _sanitize_review_output("ask @codex or @Codex to patch")
    assert sanitized == "ask Codex or Codex to patch"
    assert "@codex" not in sanitized.lower()
    for footer in (
        _manual_footer(approved=True, escalation=None, stale_head=False, truncated=False),
        _manual_footer(approved=False, escalation=None, stale_head=False, truncated=False),
        _manual_footer(approved=False, escalation="security boundary", stale_head=True, truncated=True),
    ):
        assert "@codex" not in footer
        assert "automatically" in footer or "advisory" in footer
    print("manual_review: self-test OK")


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return

    repo_root = Path(env("GITHUB_WORKSPACE", "."))
    repo = env("GITHUB_REPOSITORY", required=True)
    gh_token = env("GITHUB_TOKEN", required=True)
    raw_pr = env("REVIEW_PR_NUMBER", required=True)
    if not raw_pr.isdigit() or int(raw_pr) <= 0:
        raise RuntimeError("REVIEW_PR_NUMBER must be a positive integer")
    pr_number = int(raw_pr)

    tier = env("REVIEW_TIER", "cheap")
    if tier not in ("cheap", "senior"):
        raise RuntimeError(f"unknown REVIEW_TIER {tier!r}")
    provider = env("CHEAP_REVIEW_PROVIDER", "deepseek")
    base_url = env("CHEAP_REVIEW_BASE_URL", "https://api.deepseek.com")
    model = env("CHEAP_REVIEW_MODEL", "deepseek-chat")
    api_key = env("CHEAP_REVIEW_API_KEY", required=True)
    review_title = env("REVIEW_TITLE", "Manual senior review" if tier == "senior" else "Manual cheap review")
    diff_cap = int(env("CHEAP_REVIEW_DIFF_CAP", "60000"))
    http_timeout = float(env("REVIEW_HTTP_TIMEOUT", "180"))
    use_stream = env("REVIEW_STREAM", "false").lower() == "true"

    pr = _fetch_pr(repo, pr_number, gh_token)
    branch = str(pr["head"]["ref"])
    reviewed_sha = str(pr["head"].get("sha") or "")
    title = str(pr.get("title") or "")
    body_text = str(pr.get("body") or "")

    diff_status, diff = gh_request(
        "GET",
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}",
        gh_token,
        accept="application/vnd.github.v3.diff",
    )
    if diff_status != 200:
        raise RuntimeError(f"could not fetch PR diff (status {diff_status})")
    truncated = len(diff) > diff_cap
    if truncated:
        cut = diff.rfind("\ndiff --git", 0, diff_cap)
        diff = diff[: cut if cut > 0 else diff_cap] + "\n... [diff truncated]"

    spec_name, spec_text = resolve_spec(repo_root, branch, title, body_text)
    agents_excerpts = read_agents_sections(repo_root, AGENTS_SECTIONS)
    prompt = _manual_prompt(build_prompt(diff, spec_name, spec_text, agents_excerpts, tier))

    marker = MANUAL_COMMENT_MARKER.format(provider=provider, tier=tier)
    this_round = next_round(list_pr_comments(repo, pr_number, gh_token), marker)
    try:
        review = call_model_with_retry(
            base_url,
            model,
            api_key,
            prompt,
            timeout=http_timeout,
            stream=use_stream,
            tier=tier,
        )
    except PROVIDER_ERRORS as exc:
        detail = f"HTTP {exc.code}" if isinstance(exc, urllib.error.HTTPError) else type(exc).__name__
        post_comment(
            repo,
            pr_number,
            gh_token,
            (
                f"{marker}\n### {review_title} ({provider}) — PROVIDER ERROR\n\n"
                f"The manually requested API call failed ({detail}). No review, label, "
                "or fix request was produced. Retry only if the maintainer still wants "
                f"the external review.\n\nError detail: `{exc}`"
            ),
        )
        raise RuntimeError(f"manual review provider call failed ({detail})") from exc

    review = _sanitize_review_output(review)
    verdict = parse_verdict(review)
    approved = verdict == "NO_FURTHER_CHANGES"
    escalation = parse_escalation(review) if tier == "senior" else None
    current_sha = pr_head_sha(repo, pr_number, gh_token)
    stale_head = bool(reviewed_sha) and bool(current_sha) and current_sha != reviewed_sha
    footer = _manual_footer(
        approved=approved,
        escalation=escalation,
        stale_head=stale_head,
        truncated=truncated,
    )
    body = (
        f"{marker}\n<!-- round={this_round} -->\n"
        f"### {review_title} ({provider}) — manual run {this_round}\n\n"
        f"{review}{footer}"
    )
    post_comment(repo, pr_number, gh_token, body)


if __name__ == "__main__":
    main()
