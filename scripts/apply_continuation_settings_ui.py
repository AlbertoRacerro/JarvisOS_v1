from __future__ import annotations

from pathlib import Path

CLIENT = Path("frontend/src/api/client.ts")
PAGE = Path("frontend/src/pages/AIDraft.tsx")


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise RuntimeError(f"{path}: target is missing or ambiguous: {old[:80]!r}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_once(
        CLIENT,
        """  smoke_test_mode_enabled: boolean;
  updated_at: string;
""",
        """  smoke_test_mode_enabled: boolean;
  max_direct_continuations: number;
  max_direct_continuations_min: number;
  max_direct_continuations_max: number;
  direct_continuation_policy_version: string;
  updated_at: string;
""",
    )
    replace_once(
        PAGE,
        """      scaleway_hard_stop_token_cap: Number(form.get("scaleway_hard_stop_token_cap") ?? 800000),
      use_fake_provider_when_budget_zero: form.get("use_fake_provider_when_budget_zero") === "on"
""",
        """      scaleway_hard_stop_token_cap: Number(form.get("scaleway_hard_stop_token_cap") ?? 800000),
      max_direct_continuations: Number(form.get("max_direct_continuations") ?? 8),
      use_fake_provider_when_budget_zero: form.get("use_fake_provider_when_budget_zero") === "on"
""",
    )
    replace_once(
        PAGE,
        """              <label>
                Scaleway hard stop cap
                <input name="scaleway_hard_stop_token_cap" type="number" min="0" defaultValue={settings?.scaleway_hard_stop_token_cap ?? 800000} />
              </label>
""",
        """              <label>
                Scaleway hard stop cap
                <input name="scaleway_hard_stop_token_cap" type="number" min="0" defaultValue={settings?.scaleway_hard_stop_token_cap ?? 800000} />
              </label>
              <label>
                Direct continuation limit
                <input
                  name="max_direct_continuations"
                  type="number"
                  min={settings?.max_direct_continuations_min ?? 0}
                  max={settings?.max_direct_continuations_max ?? 16}
                  step="1"
                  defaultValue={settings?.max_direct_continuations ?? 8}
                />
                <span>
                  Server-owned per-flow snapshot · {settings?.direct_continuation_policy_version ?? "token-flow-v0"}
                </span>
              </label>
""",
    )


if __name__ == "__main__":
    main()
