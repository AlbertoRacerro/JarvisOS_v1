"""Static evidence figures (matplotlib, optional). Series colours follow a fixed
categorical order; every series also has its own marker so identity never relies on
colour alone, and every number plotted is also tabulated in the evidence report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
MARKERS = ("o", "s", "^", "D", "v")
INK, MUTED, SURFACE = "#0b0b0b", "#898781", "#fcfcfb"


def _style(plt) -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "lines.linewidth": 2, "lines.markersize": 6, "font.size": 9,
        "legend.frameon": False,
    })


def make_plots(results: dict[str, Any], out: Path) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from . import analysis

    _style(plt)
    written = []
    summary = results["summary"]
    cases = {e["result"]["name"]: e for e in results["cases"]}
    lam = sorted(summary["laminar"], key=lambda r: r["reynolds"])

    # 1. Developed velocity profile vs Hagen–Poiseuille parabola (finest mesh per Re).
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    r = np.linspace(0, 1, 200)
    ax.plot(2 * (1 - r**2), r, color=MUTED, lw=1, ls="--", label="analytic 2(1-(r/R)²)")
    for i, row in enumerate(lam):
        res = cases[row["meshes"][-1]["name"]]["result"]
        ax.plot(res["profile_u_over_umean"], res["profile_r_over_R"], ls="none", marker=MARKERS[i],
                mfc="none", color=SERIES[i], markevery=2, label=f"Re={row['reynolds']:.0f}")
    ax.set_xlabel("u / U_mean")
    ax.set_ylabel("r / R")
    ax.set_title("Laminar developed profile, finest mesh (32 radial cells)", color=INK, loc="left")
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(out / "laminar_profile.png", dpi=130)
    plt.close(fig)
    written.append("laminar_profile.png")

    # 2. Mesh convergence: |f/f_HP - 1| vs radial cells, per Re.
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    for i, row in enumerate(lam):
        n = [cases[m["name"]]["contract"]["mesh"]["radial_cells"] for m in row["meshes"]]
        err = [abs(m["darcy_f"] / row["reference"]["darcy_f"] - 1) for m in row["meshes"]]
        ax.loglog(n, err, marker=MARKERS[i], color=SERIES[i], label=f"Re={row['reynolds']:.0f}")
    n_ref = np.array([8, 32])
    ax.loglog(n_ref, 6e-3 * (n_ref / 8.0) ** -2, color=MUTED, lw=1, ls="--", label="slope −2")
    ax.set_xlabel("radial cells (axial cells refined by the same ratio 2)")
    ax.set_ylabel("|f_CFD / (64/Re) − 1|")
    ax.set_title("Laminar friction factor: mesh convergence", color=INK, loc="left")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "laminar_mesh_convergence.png", dpi=130)
    plt.close(fig)
    written.append("laminar_mesh_convergence.png")

    # 3. Friction factor vs Re: CFD vs Hagen–Poiseuille, Blasius, Colebrook.
    fig, (ax, tx) = plt.subplots(1, 2, figsize=(11, 3.9), gridspec_kw={"width_ratios": [1.2, 1]})
    re_l = np.logspace(np.log10(80), np.log10(2300), 50)
    re_t = np.logspace(np.log10(4e3), 5, 50)
    ax.loglog(re_l, 64 / re_l, color=MUTED, lw=1, ls="--", label="64/Re")
    ax.loglog(re_t, [analysis.blasius(x) for x in re_t], color=MUTED, lw=1, ls=":", label="Blasius")
    ax.loglog(re_t, [analysis.colebrook_smooth(x) for x in re_t], color=MUTED, lw=1, ls="-.",
              label="Colebrook (smooth)")
    ax.loglog(re_t, [analysis.mckeon_smooth(x) for x in re_t], color=INK, lw=0.8, ls=(0, (1, 3)),
              label="McKeon et al. 2005")
    ax.loglog([row["reynolds"] for row in lam], [row["meshes"][-1]["darcy_f"] for row in lam], ls="none",
              marker=MARKERS[0], color=SERIES[0], label="CFD laminar (finest)")
    main_turb = [t for t in summary["turbulent"] if "split" not in t["group"]]
    for i, t in enumerate(sorted(main_turb, key=lambda t: t["model"])):
        label = {"kOmegaSST": "CFD k-ω SST, y+<1 (finest)", "kEpsilon": "CFD k-ε, wall functions"}[t["model"]]
        ax.loglog([t["reynolds"]], [t["meshes"][-1]["darcy_f"]], ls="none", marker=MARKERS[i + 1],
                  color=SERIES[i + 1], label=label)
    ax.set_xlabel("Re")
    ax.set_ylabel("Darcy friction factor f")
    ax.set_title("Developed-flow friction factor", color=INK, loc="left")
    ax.legend(fontsize=7.5)

    # Right: the C1 turbulent point at readable scale, against radial resolution.
    if summary["turbulent"]:
        ref = summary["turbulent"][0]["reference"]
        for value, name, ls in ((ref["blasius_f"], "Blasius", ":"), (ref["colebrook_smooth_f"], "Colebrook", "-."),
                                (ref["mckeon_2005_f"], "McKeon 2005", (0, (1, 3)))):
            tx.axhline(value, color=MUTED, lw=1, ls=ls)
            tx.text(160, value, f" {name}", color=MUTED, fontsize=7.5, va="bottom")
        for t in summary["turbulent"]:
            n = [cases[m["name"]]["contract"]["mesh"]["radial_cells"] for m in t["meshes"]]
            f = [m["darcy_f"] for m in t["meshes"]]
            if t["model"] == "kEpsilon":
                tx.plot(n, f, ls="none", marker=MARKERS[1], color=SERIES[1], label="k-ε, wall functions (y+≈35)")
            elif "split" in t["group"]:
                tx.plot(n, f, ls="none", marker=MARKERS[3], mfc="none", ms=9, color=SERIES[3],
                        label="SST, radial or axial refined alone")
            else:
                tx.plot(n, f, marker=MARKERS[2], color=SERIES[2], label="k-ω SST, y+<1 (r, x refined ×2)")
        tx.set_xscale("log", base=2)
        tx.set_xticks([8, 15, 30, 60, 120], labels=["8", "15", "30", "60", "120"])
        tx.set_xlim(6, 400)
        tx.set_xlabel("radial cells")
        tx.set_ylabel("Darcy friction factor f")
        tx.set_title(f"C1 condition, Re = {summary['turbulent'][0]['reynolds']:.0f}", color=INK, loc="left")
        tx.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "friction_factor.png", dpi=130)
    plt.close(fig)
    written.append("friction_factor.png")

    # 4. Residual histories (one laminar, one turbulent).
    picks = [lam[-1]["meshes"][-1]["name"]] if lam else []
    picks += [t["meshes"][1]["name"] for t in main_turb if t["model"] == "kOmegaSST"]
    if picks:
        fig, axes = plt.subplots(1, len(picks), figsize=(5.2 * len(picks), 3.4), squeeze=False)
        for ax, name in zip(axes[0], picks, strict=True):
            hist = cases[name]["residual_history"]
            n_it = cases[name]["result"]["iterations"]
            for i, (var, vals) in enumerate(sorted(hist.items())):
                x = np.linspace(1, n_it, len(vals))
                ax.semilogy(x, vals, color=SERIES[i], lw=1.2, label=var)
            ax.set_xlabel("SIMPLE iteration")
            ax.set_ylabel("initial residual")
            ax.set_title(name, color=INK, loc="left")
            ax.legend(fontsize=7.5)
        fig.tight_layout()
        fig.savefig(out / "residuals.png", dpi=130)
        plt.close(fig)
        written.append("residuals.png")

    # 5. Entrance development (laminar: x/(D Re) collapses the entrance region).
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(10, 3.6))
    for i, row in enumerate(lam):
        e = cases[row["meshes"][-1]["name"]]
        d = e["contract"]["diameter_m"]
        scale = d * row["reynolds"]
        x = np.array(e["result"]["centreline_x_m"]) / scale
        ax.plot(x, e["result"]["centreline_u_over_umean"], color=SERIES[i], lw=1.4,
                label=f"Re={row['reynolds']:.0f}")
        xl = np.array(e["result"]["local_f_x_m"]) / scale
        fl = np.array(e["result"]["local_darcy_f"]) * row["reynolds"] / 64.0 - 1.0
        bx.plot(xl, 100 * fl, marker=MARKERS[i], color=SERIES[i], lw=1.2, label=f"Re={row['reynolds']:.0f}")
    for a in (ax, bx):
        a.axvline(0.05, color=MUTED, lw=1, ls="--")
        a.set_xlabel("x / (D Re)")
    ax.text(0.052, 1.05, "0.05 Re D", color=MUTED, fontsize=7.5)
    bx.axvspan(0.125, 0.2375, color="#e4e3df", alpha=0.6, lw=0)
    bx.text(0.13, 4, "measurement window", color=MUTED, fontsize=7.5)
    bx.set_ylim(-1, 8)
    ax.set_ylabel("u_axis / U_mean (axis-adjacent cell)")
    bx.set_ylabel("local f / (64/Re) − 1  [%]")
    ax.set_title("Centreline development", color=INK, loc="left")
    bx.set_title("Local pressure-gradient friction factor", color=INK, loc="left")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "laminar_development.png", dpi=130)
    plt.close(fig)
    written.append("laminar_development.png")
    return written
