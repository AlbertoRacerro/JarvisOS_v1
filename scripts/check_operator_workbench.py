from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"096 check failed: missing {label}: {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise SystemExit(f"096 check failed: forbidden {label}: {needle!r}")


def main() -> None:
    sidecar = read("frontend/src/components/shell/ContextualSidecar.tsx")
    shell_css = read("frontend/src/styles/shell.css")
    jarvis_css = read("frontend/src/components/ai/JarvisSidecar.css")
    runs = read("frontend/src/pages/RunsWorkbench.tsx")
    runs_css = read("frontend/src/styles/runs.css")
    review = read("frontend/src/stages/ReviewStage.tsx")
    app = read("frontend/src/App.tsx")

    require(sidecar, "Jarvis &amp; Properties", "single operator sidecar identity")
    require(sidecar, 'role="tablist"', "compact sidecar tabset")
    require(sidecar, 'selection.kind === "geometry-hit"', "truthful ephemeral geometry handling")
    require(sidecar, "Technical details", "machine-detail disclosure")
    forbid(sidecar, "Hydraulics", "invented engineering property semantics")
    forbid(sidecar, "Optical", "invented engineering property semantics")

    require(shell_css, "grid-template-rows: minmax(0, 42fr) minmax(0, 58fr)", "desktop Jarvis/Properties split")
    require(shell_css, "overflow: hidden", "bounded outer sidecar")
    require(shell_css, '.shell-sidecar__pane[data-compact-hidden="true"]', "compact tab visibility")
    require(jarvis_css, "overflow: hidden", "bounded Jarvis pane")
    require(jarvis_css, "flex: 1 1 auto", "scrolling transcript")

    require(runs, "View raw", "Runs raw disclosure")
    require(runs, "Technical details", "Runs machine-detail disclosure")
    require(runs_css, "max-height:min(18rem,36vh)", "bounded Runs technical region")
    require(review, '<details className="review-technical"><summary>Technical details</summary>', "Review technical disclosure")

    require(app, "const stageSidecar = shellRegions.sidecar", "stage context preservation")
    require(app, "useJarvisSidecar(workspaceId, route.id, selection)", "single App-owned Jarvis controller")
    forbid(app, "fetch(\"http", "direct frontend provider call")

    print("096 operator workbench static conformance: PASS")


if __name__ == "__main__":
    main()
