"""Fit and version a spec 216 reduced model from measured run directories.

    PYTHONPATH=backend python scripts/qualification/216/fit_reduced_model.py \
      --model-id c1_tube.darcy --runs RUN_DIR [RUN_DIR ...] \
      --mesh-study regime=turbulent_rans,fine=RUN_DIR,medium=RUN_DIR,coarse=RUN_DIR,point=RUN_DIR \
      --tolerance-laminar 0.02 --tolerance-turbulent 0.10 --out model.json

Each RUN_DIR holds ``run_report.json`` written by ``run_case.py``; the contract
it ran is read back from the case manifest and checked against the report. This
qualification command writes a candidate model file outside the repository;
it does not publish to Studio or pin a Process unit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.bluecad.cfd_pipe.casegen import MANIFEST_NAME
from app.modules.bluecad.cfd_pipe.contract import PipeStudyContract, contract_digest
from app.modules.bluecad.cfd_pipe.mesh_study import refinement_ratios, three_mesh_study
from app.modules.bluecad.cfd_pipe.reduced_model import Discretization, PublicationRefused, StudyPoint, Tolerances, publish

_REPO = Path(__file__).resolve().parents[3]


def _report(run: Path) -> dict:
    return json.loads((run / "run_report.json").read_text(encoding="utf-8"))


def _gradient(report: dict) -> float:
    comparison = report.get("laminar_comparison") or report.get("turbulent_comparison") or {}
    return float(comparison.get("pressure_gradient_pa_m", float("nan")))


def _contract(run: Path, report: dict) -> PipeStudyContract:
    manifest = json.loads((run / "case" / MANIFEST_NAME).read_text(encoding="utf-8"))
    contract = PipeStudyContract.model_validate(manifest["contract"])
    if contract_digest(contract) != report["contract_digest"]:
        raise SystemExit(f"{run}: case manifest contract does not match the run report")
    return contract


def load_point(run: Path) -> StudyPoint:
    report = _report(run)
    return StudyPoint(
        run_id=run.name, contract=_contract(run, report), case_manifest_digest=report.get("case_manifest_digest", ""),
        status=report["status"], residual_converged=bool(report.get("residual_converged")),
        pressure_gradient_pa_m=_gradient(report), tool_versions=report.get("tool_versions", {}))


def load_mesh_study(spec: str) -> Discretization:
    fields = dict(item.split("=", 1) for item in spec.split(","))
    runs = {name: Path(fields[name]) for name in ("fine", "medium", "coarse", "point")}
    reports = {name: _report(run) for name, run in runs.items()}
    cells = tuple(int(reports[name]["mesh_check"]["report"]["cells"]) for name in ("fine", "medium", "coarse"))
    values = tuple(_gradient(reports[name]) for name in ("fine", "medium", "coarse"))
    return Discretization(regime=fields["regime"], reynolds=_contract(runs["fine"], reports["fine"]).reynolds,
                          study=three_mesh_study(values, refinement_ratios(cells)),
                          point_level_value=_gradient(reports["point"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--runs", required=True, nargs="+", type=Path)
    parser.add_argument("--mesh-study", action="append", default=[])
    parser.add_argument("--tolerance-laminar", type=float, required=True)
    parser.add_argument("--tolerance-turbulent", type=float, required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.is_relative_to(_REPO):
        raise SystemExit("model output must be outside the repository")
    points = [load_point(run) for run in args.runs]
    evidence = [load_mesh_study(spec) for spec in args.mesh_study]
    tolerances = Tolerances(laminar=args.tolerance_laminar, turbulent_rans=args.tolerance_turbulent)
    try:
        model = publish(args.model_id, points, evidence, tolerances)
    except PublicationRefused as exc:
        print(json.dumps({"status": "refused", "reasons": list(exc.reasons)}, indent=2))
        return 2
    out.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(model.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
