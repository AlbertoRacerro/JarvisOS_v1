#!/usr/bin/env python3
"""Cheap-tier PR review for JarvisOS.

Calls an OpenAI-compatible chat-completions endpoint (DeepSeek by default) with a
scoped pack — PR diff, referenced spec, and the AGENTS.md hard invariants — and
posts a sticky advisory review comment. Applies a label to gate the frontier
review. Standard library only; runs inside GitHub Actions.

The review is ADVISORY. It never merges, approves, or dismisses reviews. Merge
authority is CI plus the human maintainer (see AGENTS.md "Review authority").
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GITHUB_API = "https://api.github.com"
COMMENT_MARKER = "<!-- cheap-review:{provider} -->"
DIFF_CHAR_CAP = 60_000


def die(msg: str) -> None:
    print(f"cheap_review: {msg}", file=sys.stderr)
    sys.exit(1)


def env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.environ.get(name, default)
    if required and not val:
        die(f"missing required env var {name}")
    return val or ""


def gh_request(method: str, url: str, token: str, *, accept: str, body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def read_invariants(repo_root: Path) -> str:
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("## Hard invariants"):
            capture = True
            out.append(line)
            continue
        if capture and line.startswith("## ") and not line.startswith("## Hard invariants"):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def resolve_spec(repo_root: Path, branch: str, title: str) -> tuple[str, str]:
    """Return (spec_name, spec_text) or ('', '') if none is referenced."""
    m = re.search(r"(\d{3})", branch) or re.search(r"spec[ -]?(\d{3})", title, re.I)
    if not m:
        return "", ""
    num = m.group(1)
    matches = sorted((repo_root / "docs" / "specs").glob(f"{num}-*.md"))
    if not matches:
        return "", ""
    return matches[0].name, matches[0].read_text(encoding="utf-8")


def build_prompt(diff: str, spec_name: str, spec_text: str, invariants: str) -> str:
    spec_block = (
        f"Referenced spec `{spec_name}`:\n\n{spec_text}"
        if spec_name
        else "No spec file was resolved from the branch/title. If this PR is not "
        "pure docs/infra, that itself is a MAJOR finding."
    )
    return f"""You are the cheap-tier code reviewer for JarvisOS. Your review is
ADVISORY ONLY: you have no merge, approve, or dismiss authority. Never claim you
do. Merge authority is CI plus the human maintainer.

Review the PR diff strictly for substance, not style:
- Violations of the hard invariants below -> CRITICAL.
- Spec conformance: acceptance criteria met, scope respected, binding non-goals
  untouched, out-of-scope files justified -> MAJOR.
- Real correctness bugs, each with a concrete failure scenario.
- Required tests present, offline-only (no live providers/Ollama/network),
  assertions meaningful.
Do NOT report style nits unless they violate an AGENTS.md convention.

Output format, EXACTLY:
- First line: `VERDICT: NEEDS_CHANGES` or `VERDICT: NO_FURTHER_CHANGES`.
- Then a short findings list, each line `CRITICAL|MAJOR|MINOR: <file> - <one-line
  failure scenario>`. If none, write `No blocking findings.`
- Then one or two sentences on what you verified.
Use NO_FURTHER_CHANGES only when there are zero CRITICAL and zero MAJOR findings.

=== HARD INVARIANTS (AGENTS.md) ===
{invariants}

=== SPEC ===
{spec_block}

=== PR DIFF ===
{diff}
"""


def call_model(base_url: str, model: str, api_key: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "stream": False,
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.loads(resp.read().decode())
    return payload["choices"][0]["message"]["content"].strip()


def find_sticky(repo: str, pr: int, token: str, marker: str) -> tuple[int | None, int]:
    """Return (comment_id or None, prior_round_count)."""
    status, text = gh_request(
        "GET",
        f"{GITHUB_API}/repos/{repo}/issues/{pr}/comments?per_page=100",
        token,
        accept="application/vnd.github+json",
    )
    if status != 200:
        return None, 0
    for c in json.loads(text):
        if marker in c.get("body", ""):
            rounds = re.search(r"round=(\d+)", c["body"])
            return c["id"], int(rounds.group(1)) if rounds else 0
    return None, 0


def upsert_comment(repo: str, pr: int, token: str, comment_id: int | None, body: str) -> None:
    if comment_id is not None:
        gh_request(
            "PATCH",
            f"{GITHUB_API}/repos/{repo}/issues/comments/{comment_id}",
            token,
            accept="application/vnd.github+json",
            body={"body": body},
        )
    else:
        gh_request(
            "POST",
            f"{GITHUB_API}/repos/{repo}/issues/{pr}/comments",
            token,
            accept="application/vnd.github+json",
            body={"body": body},
        )


def set_label(repo: str, pr: int, token: str, label: str, present: bool) -> None:
    # Remove first (idempotent); re-add only when approved, so each approved push
    # re-fires the `labeled` event that gates the frontier review.
    gh_request(
        "DELETE",
        f"{GITHUB_API}/repos/{repo}/issues/{pr}/labels/{urllib.parse.quote(label)}",
        token,
        accept="application/vnd.github+json",
    )
    if present:
        gh_request(
            "POST",
            f"{GITHUB_API}/repos/{repo}/issues/{pr}/labels",
            token,
            accept="application/vnd.github+json",
            body={"labels": [label]},
        )


def main() -> None:
    provider = env("CHEAP_REVIEW_PROVIDER", "deepseek")
    base_url = env("CHEAP_REVIEW_BASE_URL", "https://api.deepseek.com")
    model = env("CHEAP_REVIEW_MODEL", "deepseek-chat")
    api_key = env("CHEAP_REVIEW_API_KEY", required=True)
    gh_token = env("GITHUB_TOKEN", required=True)
    repo = env("GITHUB_REPOSITORY", required=True)
    label = env("FRONTIER_LABEL", "frontier-review")
    round_limit = int(env("ROUND_LIMIT", "3"))
    repo_root = Path(env("GITHUB_WORKSPACE", "."))

    event = json.loads(Path(env("GITHUB_EVENT_PATH", required=True)).read_text())
    pr = event["pull_request"]["number"]
    branch = event["pull_request"]["head"]["ref"]
    title = event["pull_request"].get("title", "")

    marker = COMMENT_MARKER.format(provider=provider)
    comment_id, prior_rounds = find_sticky(repo, pr, gh_token, marker)
    this_round = prior_rounds + 1

    if this_round > round_limit:
        body = (
            f"{marker}\n<!-- round={prior_rounds} -->\n"
            f"### Cheap-tier review ({provider}) — ROUND LIMIT REACHED\n\n"
            f"Reached the {round_limit}-round limit. Maintainer decision needed; "
            "no further @codex iterations from the cheap tier."
        )
        upsert_comment(repo, pr, gh_token, comment_id, body)
        set_label(repo, pr, gh_token, label, present=False)
        return

    diff_status, diff = gh_request(
        "GET",
        f"{GITHUB_API}/repos/{repo}/pulls/{pr}",
        gh_token,
        accept="application/vnd.github.v3.diff",
    )
    if diff_status != 200:
        die(f"could not fetch PR diff (status {diff_status})")
    truncated = len(diff) > DIFF_CHAR_CAP
    if truncated:
        diff = diff[:DIFF_CHAR_CAP] + "\n... [diff truncated]"

    spec_name, spec_text = resolve_spec(repo_root, branch, title)
    invariants = read_invariants(repo_root)
    prompt = build_prompt(diff, spec_name, spec_text, invariants)

    try:
        review = call_model(base_url, model, api_key, prompt)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
        body = (
            f"{marker}\n<!-- round={prior_rounds} -->\n"
            f"### Cheap-tier review ({provider}) — PROVIDER ERROR\n\n"
            f"The {provider} API call failed (`{type(exc).__name__}`). Review was "
            "not produced. Apply the `frontier-review` label manually to proceed."
        )
        upsert_comment(repo, pr, gh_token, comment_id, body)
        return  # fail-open: do not block the PR

    approved = review.splitlines()[0].strip().upper().startswith("VERDICT: NO_FURTHER_CHANGES")
    footer = (
        "\n\n@codex please fix the review findings above on this branch, then wait "
        "for re-review."
        if not approved
        else "\n\n_Cheap tier is satisfied. This is a trigger for frontier review, "
        "not an approval; the maintainer merges._"
    )
    note = "\n\n_Diff was truncated for review._" if truncated else ""
    body = (
        f"{marker}\n<!-- round={this_round} -->\n"
        f"### Cheap-tier review ({provider}) — round {this_round}/{round_limit}\n\n"
        f"{review}{note}{footer}"
    )
    upsert_comment(repo, pr, gh_token, comment_id, body)
    set_label(repo, pr, gh_token, label, present=approved)


if __name__ == "__main__":
    main()
