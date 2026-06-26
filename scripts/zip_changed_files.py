"""Create a review zip containing only changed source/report files.

The helper is intentionally small: it reads changed paths from git, filters
obvious generated/binary/secret artifacts, and writes repo-relative paths into
reports/<milestone>/changed_files.zip.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
import zipfile
from pathlib import Path


DEFAULT_MAX_FILE_BYTES = 1_048_576
OUTPUT_ZIP_NAME = "changed_files.zip"
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    ".cache",
}
SECRET_BASENAME_PATTERNS = {
    ".env",
    ".env.*",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials.json",
    "credential.json",
    "tokens.json",
    "token.json",
    "secrets.json",
    "secret.json",
}
SECRET_EXTENSIONS = {".pem", ".key", ".p12", ".pfx"}
BINARY_ARCHIVE_MEDIA_EXTENSIONS = {
    ".zip",
    ".db",
    ".sqlite",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".mp4",
    ".mov",
    ".exe",
    ".dll",
    ".pyd",
    ".so",
}


def run_git(args: list[str], repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed with exit {completed.returncode}\n{completed.stderr.strip()}"
        )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def repo_root_from_cwd() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("must be run inside a git repository")
    return Path(completed.stdout.strip()).resolve()


def normalize_git_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def changed_paths_for_range(repo_root: Path, base: str, head: str) -> list[str]:
    return run_git(["diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}"], repo_root)


def changed_paths_uncommitted(repo_root: Path) -> list[str]:
    diff_paths = run_git(["diff", "--name-only", "--diff-filter=ACMR", "HEAD"], repo_root)
    untracked_paths = run_git(["ls-files", "--others", "--exclude-standard"], repo_root)
    return [*diff_paths, *untracked_paths]


def dedupe_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for path in paths:
        normalized = normalize_git_path(path)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return sorted(deduped)


def has_excluded_dir(path: str) -> str | None:
    for part in Path(path).parts:
        if part in EXCLUDED_DIR_NAMES:
            return part
    return None


def is_secret_artifact_basename(name: str) -> bool:
    lowered = name.lower()
    return any(fnmatch.fnmatchcase(lowered, pattern) for pattern in SECRET_BASENAME_PATTERNS)


def skip_reason(path: str, repo_root: Path, max_file_bytes: int) -> str | None:
    normalized = normalize_git_path(path)
    excluded_dir = has_excluded_dir(normalized)
    if excluded_dir is not None:
        return f"excluded directory: {excluded_dir}"

    full_path = (repo_root / normalized).resolve()
    try:
        full_path.relative_to(repo_root)
    except ValueError:
        return "path escapes repository root"

    if not full_path.exists():
        return "file does not exist"
    if not full_path.is_file():
        return "not a regular file"

    basename = full_path.name
    suffix = full_path.suffix.lower()
    if is_secret_artifact_basename(basename):
        return "secret artifact basename"
    if suffix in SECRET_EXTENSIONS:
        return f"secret artifact extension: {suffix}"
    if suffix in BINARY_ARCHIVE_MEDIA_EXTENSIONS:
        return f"binary/archive/database/media extension: {suffix}"

    size = full_path.stat().st_size
    if size > max_file_bytes:
        return f"file exceeds max size: {size} > {max_file_bytes}"
    return None


def collect_eligible_files(paths: list[str], repo_root: Path, max_file_bytes: int) -> tuple[list[str], list[tuple[str, str]]]:
    included: list[str] = []
    skipped: list[tuple[str, str]] = []
    for path in dedupe_paths(paths):
        reason = skip_reason(path, repo_root, max_file_bytes)
        if reason is None:
            included.append(path)
        else:
            skipped.append((path, reason))
    return included, skipped


def milestone_dir(repo_root: Path, milestone: str) -> Path:
    if not milestone or any(separator in milestone for separator in ("/", "\\")) or milestone in {".", ".."}:
        raise SystemExit("milestone must be a single path segment")
    if ".." in Path(milestone).parts:
        raise SystemExit("milestone must not contain parent path segments")
    return repo_root / "reports" / milestone


def write_zip(included: list[str], repo_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(repo_root / path, arcname=path)


def print_report(zip_path: Path, included: list[str], skipped: list[tuple[str, str]]) -> None:
    print(f"zip path: {zip_path}")
    print(f"files included: {len(included)}")
    print("included files:")
    if included:
        for path in included:
            print(f"  {path}")
    else:
        print("  (none)")
    print("skipped files:")
    if skipped:
        for path, reason in skipped:
            print(f"  {path} -- {reason}")
    else:
        print("  (none)")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zip added/copied/modified/renamed files for review.")
    parser.add_argument("--milestone", required=True, help="Milestone ID used under reports/<MILESTONE_ID>.")
    parser.add_argument("--base", help="Base commit/ref for committed range mode.")
    parser.add_argument("--head", help="Head commit/ref for committed range mode.")
    parser.add_argument("--uncommitted", action="store_true", help="Zip tracked and untracked uncommitted files.")
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    args = parser.parse_args(argv)

    range_args_present = bool(args.base or args.head)
    if args.uncommitted == range_args_present:
        parser.error("choose exactly one mode: --uncommitted or --base <BASE> --head <HEAD>")
    if range_args_present and not (args.base and args.head):
        parser.error("--base and --head must be provided together")
    if args.max_file_bytes <= 0:
        parser.error("--max-file-bytes must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = repo_root_from_cwd()
    if args.uncommitted:
        candidate_paths = changed_paths_uncommitted(repo_root)
    else:
        candidate_paths = changed_paths_for_range(repo_root, args.base, args.head)

    included, skipped = collect_eligible_files(candidate_paths, repo_root, args.max_file_bytes)
    output_dir = milestone_dir(repo_root, args.milestone)
    output_path = output_dir / OUTPUT_ZIP_NAME

    if included:
        write_zip(included, repo_root, output_path)
    else:
        print("no eligible files found; zip was not created")
    print_report(output_path, included, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
