"""Offline, synthetic spec 103 qualification probes.

Run with /home/thera/jarvis-control/work/venvs/q103/bin/python
scripts/qualification/103/probe.py. Each candidate gets an independent result.
These probes measure numerical/API feasibility, not scientific validity.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
OUT = Path(__file__).resolve().parent / "results"
T = 298.15  # K; synthetic PBR screening point
P = 101325.0  # Pa


def coolprop():
    from CoolProp.CoolProp import PropsSI

    return {"water_density_kg_m3": PropsSI("D", "T", T, "P", P, "Water"),
            "water_viscosity_Pa_s": PropsSI("V", "T", T, "P", P, "Water"),
            "co2_density_kg_m3": PropsSI("D", "T", T, "P", P, "CO2"),
            "water_saturation_pressure_Pa": PropsSI("P", "T", T, "Q", 0, "Water")}


def chemicals():
    from chemicals.iapws import iapws95_rho
    from chemicals.vapor_pressure import Antoine

    # IAPWS density and Antoine water coefficients for T in degrees C, mmHg.
    return {"water_density_kg_m3": iapws95_rho(T, P),
            "water_saturation_pressure_Pa": Antoine(T-273.15, 8.07131, 1730.63, 233.426, base=10.0) * 133.322}


def thermo():
    from thermo import Chemical, Mixture

    water = Chemical("water", T=T, P=P)
    co2 = Chemical("carbon dioxide", T=T, P=P)
    brine = Mixture(["water", "sodium chloride"], ws=[0.965, 0.035], T=T, P=P)
    return {"water_density_kg_m3": water.rho, "co2_density_kg_m3": co2.rho,
            "brine_density_kg_m3": brine.rho, "water_phase": water.phase,
            "co2_phase": co2.phase, "brine_phase": brine.phase}


def fluids():
    from app.modules.process_kernel.blocks import Pipe
    from app.modules.process_kernel.streams import MaterialStream
    from fluids.friction import friction_factor

    density, mu, velocity, diameter, length = 997.0, 0.00089, 1.0, 0.05, 10.0
    incumbent = Pipe().solve({"inlet": MaterialStream("water", density_kg_m3=density,
                                dynamic_viscosity_Pa_s=mu)}, {},
                             {"tube_length": length, "tube_inner_diameter": diameter * 1000,
                              "tube_outer_diameter": 60.0, "target_liquid_velocity": velocity}, {})
    old = incumbent.scalar_outputs
    re = density * velocity * diameter / mu
    new_f = friction_factor(Re=re, eD=0.0)
    new_dp = new_f * length / diameter * density * velocity**2 / 2
    return {"reynolds_number": re, "friction_factor_darcy": new_f,
            "pressure_loss_Pa": new_dp, "incumbent_friction_factor_darcy": old["friction_factor"],
            "incumbent_pressure_loss_Pa": old["major_pressure_loss"],
            "pressure_loss_relative_difference": (new_dp-old["major_pressure_loss"])/old["major_pressure_loss"]}


def ht():
    from ht.conv_internal import turbulent_Dittus_Boelter

    re, pr, conductivity, diameter = 56011.0, 6.2, 0.6, 0.05
    nu = turbulent_Dittus_Boelter(re, pr)
    return {"nusselt": nu, "heat_transfer_coefficient_W_m2_K": nu * conductivity / diameter,
            "incumbent": "047 has no heat-transfer correlation"}


def thermosteam():
    import thermosteam as tmo

    tmo.settings.set_thermo(["Water", "CO2"])
    stream = tmo.Stream("water_co2", Water=100, CO2=1, units="kg/hr", T=T, P=P)
    return {"phase": stream.phase, "mass_flow_kg_hr": stream.F_mass,
            "water_mass_flow_kg_hr": stream.imass["Water"], "co2_mass_flow_kg_hr": stream.imass["CO2"]}


def biosteam():
    import biosteam as bst

    bst.settings.set_thermo(["Water", "CO2"])
    fresh = bst.Stream("fresh103", Water=100, units="kg/hr")
    recycle = bst.Stream("recycle103")
    mixer = bst.Mixer("mix103", ins=(fresh, recycle))
    splitter = bst.Splitter("split103", ins=mixer-0, outs=("product103", recycle), split=0.2)
    # A splitter is the synthetic separator: 20% product, 80% recycled.
    system = bst.System("recycle_system103", path=(mixer, splitter), recycle=recycle)
    system.simulate()
    return {"fresh_kg_hr": fresh.F_mass, "mixed_kg_hr": mixer.outs[0].F_mass,
            "product_kg_hr": splitter.outs[0].F_mass, "recycle_kg_hr": recycle.F_mass,
            "mass_balance_error_kg_hr": fresh.F_mass-splitter.outs[0].F_mass,
            "expected_recycle_kg_hr": 400.0}


def qsdsan():
    import qsdsan as qs

    # Package-specific stream construction, avoiding global flowsheet/TEA state.
    s = qs.WasteStream("synthetic_water103", H2O=100, units="kg/hr")
    return {"water_mass_flow_kg_hr": s.imass["H2O"], "total_mass_flow_kg_hr": s.F_mass}


def pyomo():
    import pyomo.environ as pyo

    available = {name: bool(pyo.SolverFactory(name).available(exception_flag=False))
                 for name in ("ipopt", "appsi_ipopt", "glpk", "cbc", "highs")}
    if not any(available.values()):
        raise RuntimeError(f"No local Pyomo solver available: {available}")
    model = pyo.ConcreteModel()
    model.x = pyo.Var(bounds=(0, 10), initialize=2)
    model.obj = pyo.Objective(expr=(model.x-3)**2)
    solver = next(name for name, ok in available.items() if ok)
    result = pyo.SolverFactory(solver).solve(model)
    return {"solver": solver, "termination": str(result.solver.termination_condition),
            "x": pyo.value(model.x), "solvers_available": available}


def idaes():
    os.environ.setdefault("IDAES_DATA", "/tmp/q103-idaes")
    import idaes
    import pyomo.environ as pyo

    available = pyo.SolverFactory("ipopt").available(exception_flag=False)
    if not available:
        raise RuntimeError("IDAES IPOPT unavailable locally; idaes get-extensions requires network")
    return {"idaes_version": idaes.__version__, "ipopt_available": available}


def watertap():
    import pyomo.environ as pyo
    import watertap

    available = pyo.SolverFactory("ipopt").available(exception_flag=False)
    if not available:
        raise RuntimeError("WaterTAP flowsheet solve unavailable: IPOPT binary absent")
    return {"imported": watertap is not None, "ipopt_available": available}


def rhs(t, y):
    light = max(0.0, math.sin(2 * math.pi * (t % 24) / 24))
    return (0.08 * light - 0.025) * y


def sundae():
    import numpy as np
    from sksundae.cvode import CVODE
    from sksundae.ida import IDA

    def native_rhs(t, y, yp):
        yp[0] = rhs(t, y[0])

    t = np.linspace(0, 48, 97)
    result = CVODE(native_rhs, rtol=1e-9, atol=1e-11).solve(t, np.array([1.0]))
    def dae_residual(hour, y, yp, residual):
        residual[0] = yp[0] - rhs(hour, y[1])
        residual[1] = y[1] - y[0]  # algebraic instantaneous mixed inventory

    dae = IDA(dae_residual, algebraic_idx=[1], rtol=1e-8, atol=1e-10).solve(
        t, np.array([1.0, 1.0]), np.array([-0.025, 0.0]))
    return {"success": bool(result.success), "final_biomass_arbitrary": float(result.y[-1, 0]),
            "minimum_biomass_arbitrary": float(result.y[:, 0].min()), "time_points": len(result.t),
            "dae_success": bool(dae.success), "dae_final_biomass_arbitrary": float(dae.y[-1, 0]),
            "dae_max_algebraic_residual": float(np.max(np.abs(dae.y[:, 1]-dae.y[:, 0]))),
            "fixture": "synthetic periodic growth/loss ODE; not biology validation"}


def casadi():
    import casadi as ca

    x = ca.MX.sym("x")
    light = ca.MX.sym("light")
    # CasADi owns the symbolic RHS; this probe owns fixed-step integration time.
    f = ca.Function("step_rhs", [x, light], [(0.08 * light - 0.025) * x])
    z = ca.MX.sym("mixed_inventory")
    ida = ca.integrator("dae_step", "idas", {"x": x, "z": z, "p": light,
                                               "ode": (0.08*light-0.025)*z, "alg": z-x}, 0, 0.25)
    state = 1.0
    dae_state = 1.0
    dae_residual = 0.0
    dt = 0.25
    for step in range(192):
        t = step * dt
        illumination = lambda hour: max(0.0, math.sin(2 * math.pi * hour / 24))
        k1 = float(f(state, illumination(t)))
        k2 = float(f(state + dt*k1/2, illumination(t+dt/2)))
        k3 = float(f(state + dt*k2/2, illumination(t+dt/2)))
        k4 = float(f(state + dt*k3, illumination(t+dt)))
        state += dt * (k1 + 2*k2 + 2*k3 + k4) / 6
        dae_step = ida(x0=dae_state, z0=dae_state, p=illumination(t+dt/2))
        dae_state = float(dae_step["xf"])
        dae_residual = max(dae_residual, abs(float(dae_step["zf"])-dae_state))
    return {"final_biomass_arbitrary": state, "symbolic_graph_nodes": int(ca.n_nodes(f(x, light))),
            "dae_final_biomass_arbitrary": dae_state, "dae_max_algebraic_residual": dae_residual,
            "method": "symbolic RHS with fixed-step RK4; IDAS DAE midpoint light; 0.25 hour steps"}


def dompc():
    import do_mpc

    model = do_mpc.model.Model("discrete")
    x = model.set_variable("_x", "inventory")
    u = model.set_variable("_u", "harvest")
    model.set_rhs("inventory", x + 0.1 - u)
    model.setup()
    mpc = do_mpc.controller.MPC(model)
    mpc.set_param(n_horizon=3, t_step=1, store_full_solution=False)
    mpc.set_objective(mterm=(x-1)**2, lterm=(x-1)**2)
    mpc.set_rterm(harvest=0.1)
    mpc.bounds["lower", "_u", "harvest"] = 0
    mpc.bounds["upper", "_u", "harvest"] = 0.2
    mpc.setup()
    return {"model_state_count": model.n_x, "mpc_horizon": 3,
            "solver_execution": "not attempted; requires IPOPT for optimization"}


def fmpy():
    import fmpy
    from fmpy import examples

    # An installed reference FMU would be needed for a real round trip.
    raise RuntimeError(f"No offline reference FMU/compiler provided; fmpy={fmpy.__version__}, examples={examples.__file__}")


def openmdao():
    import openmdao.api as om

    problem = om.Problem(reports=False)
    problem.model.add_subsystem("pump", om.ExecComp("pump_w=flow*head/eff", flow=1.0, head=1.0,
                                                     eff=0.8, pump_w=1.0), promotes=["*"])
    problem.driver = om.ScipyOptimizeDriver()
    problem.model.add_design_var("flow", lower=0.1, upper=2.0)
    problem.model.add_objective("pump_w")
    problem.setup()
    problem.set_val("head", 10.0)
    problem.run_driver()
    return {"flow": float(problem.get_val("flow")[0]),
            "power": float(problem.get_val("pump_w")[0]), "driver": "ScipyOptimizeDriver"}


def neqsim():
    from neqsim.thermo import fluid

    system = fluid("srk")
    system.addComponent("water", 1.0)
    system.addComponent("CO2", 0.01)
    system.setTemperature(T)
    system.setPressure(P / 100000)
    system.init(0)
    return {"components": 2, "phase_count": int(system.getNumberOfPhases())}


PROBES = {
    "CoolProp": coolprop, "chemicals": chemicals, "thermo": thermo,
    "fluids": fluids, "ht": ht, "thermosteam": thermosteam,
    "biosteam": biosteam, "qsdsan": qsdsan, "pyomo": pyomo,
    "idaes-pse": idaes, "watertap": watertap, "scikit-sundae": sundae,
    "casadi": casadi, "do-mpc": dompc, "fmpy": fmpy,
    "openmdao": openmdao, "neqsim": neqsim,
}
PREREQUISITE_CHECKS = {"pyomo", "idaes-pse", "watertap", "fmpy"}


def run():
    OUT.mkdir(exist_ok=True)
    for name, probe in PROBES.items():
        dist = metadata.distribution(name)
        license_text = (dist.metadata.get("License-Expression") or dist.metadata.get("License")
                        or next((c.rsplit("::", 1)[-1].strip() for c in dist.metadata.get_all("Classifier", [])
                                 if c.startswith("License ::")), "not declared in metadata"))
        started = time.perf_counter()
        record = {"candidate": name, "version": dist.version, "license": license_text,
                  "status": "succeeded", "wall_time_s": 0.0}
        try:
            record["measurements"] = probe()
        except Exception as exc:  # noqa: BLE001 - preserve each package's native failure
            record["status"] = "failed"
            record["native_error"] = f"{type(exc).__module__}.{type(exc).__name__}: {exc}"
            record["error_source"] = "prerequisite_check" if name in PREREQUISITE_CHECKS else "package"
        record["wall_time_s"] = round(time.perf_counter() - started, 6)
        (OUT / f"{name}.json").write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(name, record["status"], record.get("native_error", ""))


if __name__ == "__main__":
    run()
