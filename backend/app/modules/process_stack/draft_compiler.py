"""Deterministic DWSIM materialization of one Jarvis draft revision, verified by read-back (spec 155).

``expected`` derives the normalized materialization from the draft alone. ``plan`` lists the
exact MCP calls. ``materialize`` executes the plan in a fresh flowsheet, reads the result back
from the live MCP and the saved native case, normalizes it, and compares field by field. Any
difference refuses the solve with per-path diagnostics; the fingerprint is the digest of the
normalized read-back, so the same revision and tool versions give the same fingerprint.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree

from app.modules.process_stack.draft_models import COMPILER_VERSION, STREAM_SPECS, UNIT_REGISTRY
from app.modules.process_stack.dwsim import _mass_balance
from app.modules.process_stack.dwsim_mcp import DwsimMcpClient, DwsimMcpError

_REL_TOL = 1e-7
_ABS_TOL = 1e-9
_NATIVE_TO_TYPE = {native: spec.type for spec in UNIT_REGISTRY.values() for native in spec.native_types}


class MaterializationError(RuntimeError):
    def __init__(self, code: str, message: str, **detail: Any):
        super().__init__(message)
        self.code, self.detail = code, detail


def _streams(document: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((item for item in document["objects"].values() if item["kind"] == "stream"),
                  key=lambda item: item["tag"])


def _material_streams(document: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _streams(document) if item["type"] != "EnergyStream"]


def _energy_streams(document: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _streams(document) if item["type"] == "EnergyStream"]


def _native_energy_port(unit: dict[str, Any], port: int) -> int:
    return port + (10 if unit["type"] == "DistillationColumn" else
                   1 if unit["type"] in {"Heater", "Cooler", "PFR"} else 0)


def _units(document: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((item for item in document["objects"].values() if item["kind"] == "unit"),
                  key=lambda item: item["tag"])


def _composition(document: dict[str, Any], stream: dict[str, Any]) -> dict[str, float]:
    given = stream["spec"].get("composition", {})
    return {name: float(given.get(name, 0.0)) for name in document["compounds"]}


def _mole_basis(stream: dict[str, Any]) -> bool:
    return stream["spec"].get("composition_basis") == "mole"


def _feed_expected(document: dict[str, Any], stream: dict[str, Any]) -> dict[str, Any]:
    """Normalized feed as DWSIM must hold it: the chosen alternative of each group, never both.

    Pressure plus temperature or vapor fraction, mass or molar flow, mass or mole fractions. A
    vapor-fraction feed also expects DWSIM's ``Pressure_and_VaporFraction`` stream spec and a
    molar-flow feed the ``Mole`` defined flow, both read back from the saved native case.
    """
    spec = stream["spec"]
    feed: dict[str, Any] = {}
    for key, (_kind, arg, _label) in STREAM_SPECS.items():
        if key in spec:
            feed[arg] = float(spec[key]["si"])
    if "vapor_fraction" in spec:
        feed["spec_type"] = "Pressure_and_VaporFraction"
    if "molar_flow" in spec:
        feed["defined_flow"] = "Mole"
    feed["mole_composition" if _mole_basis(stream) else "composition"] = _composition(document, stream)
    return feed


def _feed_calls(document: dict[str, Any], stream: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """MCP calls that materialize one feed, in the order the spec 162 probe proved on DWSIM 10.2.9.

    ``dwsim_stream_add_material`` ignores its flow and vapor-fraction arguments, so flows go through
    ``dwsim_stream_set_conditions`` (a zero flow through the stream's ``PROP_MS_2``/``PROP_MS_3``,
    which set_conditions skips), mole fractions through ``PROP_MS_102/<compound>``, and a vapor
    fraction through ``SpecType`` + ``PROP_MS_27`` after the flow (set_conditions resets it).
    """
    spec, tag = stream["spec"], stream["tag"]
    add: dict[str, Any] = {"name": tag, "pressure_Pa": float(spec["pressure"]["si"])}
    if "temperature" in spec:
        add["temperature_K"] = float(spec["temperature"]["si"])
    composition = _composition(document, stream)
    if not _mole_basis(stream):
        add["composition"] = composition
    calls: list[tuple[str, dict[str, Any]]] = [("dwsim_stream_add_material", add)]
    if _mole_basis(stream):
        calls.append(("dwsim_unitop_set", {"name": tag, "properties": {
            f"PROP_MS_102/{name}": value for name, value in composition.items()}}))
    flow_key = "molar_flow" if "molar_flow" in spec else "mass_flow"
    flow = float(spec[flow_key]["si"])
    if flow == 0.0:
        calls.append(("dwsim_unitop_set", {"name": tag, "properties": {
            "PROP_MS_3" if flow_key == "molar_flow" else "PROP_MS_2": 0.0}}))
    else:
        calls.append(("dwsim_stream_set_conditions", {"name": tag, STREAM_SPECS[flow_key][1]: flow}))
    if "vapor_fraction" in spec:
        calls.append(("dwsim_unitop_set", {"name": tag, "properties": {
            "SpecType": "Pressure_and_VaporFraction", "PROP_MS_27": float(spec["vapor_fraction"]["si"])}}))
    return calls


def _unit_properties(unit: dict[str, Any]) -> dict[str, Any]:
    spec = UNIT_REGISTRY[unit["type"]]
    if not spec.modes:
        return {}
    properties: dict[str, Any] = {}
    if unit["type"] == "PFR":
        properties["ReactorOperationMode"] = spec.modes[unit["mode"]]
    elif unit["type"] == "Splitter":
        properties["OperationMode"] = spec.modes[unit["mode"]]
    elif unit["type"] == "HeatExchanger":
        properties["CalculationMode"] = spec.modes[unit["mode"]]
    elif unit["type"] != "DistillationColumn":
        properties["CalcMode"] = spec.modes[unit["mode"]]
    for param in spec.params_for(unit["mode"]):
        key = "__CondenserSpec" if param.key == "condenser_spec" else "__ReboilerSpec" if param.key == "reboiler_spec" else param.dwsim_property
        if unit["type"] == "Splitter" and param.key.startswith("split_ratio_"):
            key = f"__SplitRatio{param.key[-1]}"
        properties[key] = float(unit["params"][param.key]["si"])
    if unit["type"] == "DistillationColumn":
        properties.update(CondenserType="Total_Condenser", MaxIterations=500)
    if unit["type"] == "PFR" and unit.get("reactions"):
        properties["__ReactionSetID"] = f"JARVIS_{unit['tag']}"
    return properties


def _child(parent: ElementTree.Element, path: str) -> ElementTree.Element:
    node = parent.find(path)
    if node is None:
        raise MaterializationError("native_shape", f"DWSIM native element {path} is unavailable")
    return node


def _patch_native_xml(case_path: Path, document: dict[str, Any]) -> None:
    """Materialize proven native details absent from the pinned MCP connector."""
    if not any(unit["type"] == "DistillationColumn" or unit["type"] == "PFR" and unit.get("reactions")
               for unit in _units(document)):
        return
    tree = ElementTree.parse(case_path)
    root = tree.getroot()
    graphics = {node.findtext("Tag"): node for node in root.findall("./GraphicObjects/GraphicObject")}
    native_by_tag = {tag: node.findtext("Name") or "" for tag, node in graphics.items()}
    simulations = {node.findtext("Name"): node for node in root.findall("./SimulationObjects/SimulationObject")}

    for unit in (item for item in _units(document) if item["type"] == "PFR" and item.get("reactions")):
        reaction_root = root.find("Reactions")
        set_root = root.find("ReactionSets")
        if reaction_root is None or set_root is None:
            raise MaterializationError("reaction_native_shape", "DWSIM reaction template is unavailable")
        set_id = f"JARVIS_{unit['tag']}"
        selected = unit["reactions"]
        for reaction_id in selected:
            data = document["reactions"][reaction_id]
            forward = data["A_forward"]
            activation = data["E_forward"]
            reaction = ElementTree.SubElement(reaction_root, "Reaction")
            def sub(parent: ElementTree.Element, name: str, value: str = "") -> ElementTree.Element:
                child = ElementTree.SubElement(parent, name)
                child.text = value
                return child
            sub(reaction, "Type", "DWSIM.Thermodynamics.BaseClasses.Reaction")
            sub(reaction, "BaseReactant", data["base_reactant"])
            sub(reaction, "Description")
            sub(reaction, "Equation", " + ".join(data["stoichiometry"]))
            sub(reaction, "ID", reaction_id)
            sub(reaction, "Name", data["name"])
            sub(reaction, "ReactionBasis", data["basis"])
            sub(reaction, "ReactionHeat", "0")
            sub(reaction, "ReactionHeatCO", "0")
            sub(reaction, "ReactionPhase", data["phase"])
            sub(reaction, "ReactionType", "Kinetic")
            sub(reaction, "StoichBalance", "0")
            sub(reaction, "A_Forward", str(forward["value"]))
            for name, value in (("A_Reverse", "0"), ("Approach", "0"), ("ConcUnit", "kmol/m3"),
                                ("ConstantKeqValue", "0"), ("E_Forward", str(activation["value"])),
                                ("E_Reverse", "0"), ("Expression", ""), ("KExprType", "Gibbs"),
                                ("Kvalue", "0"), ("Rate", "0"), ("ReactionGibbsEnergy", "0"),
                                ("Tmax", "2000"), ("Tmin", "0"), ("VelUnit", forward["unit"]),
                                ("ReactionKinFwdType", "Arrhenius"), ("ReactionKinRevType", "Arrhenius"),
                                ("ReactionKinFwdExpression", ""), ("ReactionKinRevExpression", ""),
                                ("E_Forward_Unit", activation["unit"]), ("E_Reverse_Unit", "J/mol")):
                sub(reaction, name, value)
            compounds_node = sub(reaction, "Compounds")
            for compound, coefficient in sorted(data["stoichiometry"].items()):
                ElementTree.SubElement(compounds_node, "Compound", {
                    "Name": compound, "StoichCoeff": str(coefficient),
                    "DirectOrder": str(data["orders"].get(compound, 1.0 if compound == data["base_reactant"] else 0.0)),
                    "ReverseOrder": "0", "IsBaseReactant": str(compound == data["base_reactant"]).lower(),
                })
        reaction_set = ElementTree.SubElement(set_root, "ReactionSet")
        for key, value in (("ID", set_id), ("Name", set_id), ("Description", "")):
            child = ElementTree.SubElement(reaction_set, key)
            child.text = value
        reactions_node = ElementTree.SubElement(reaction_set, "Reactions")
        for rank, reaction_id in enumerate(selected):
            ElementTree.SubElement(reactions_node, "Reaction", {"Key": reaction_id, "ReactionID": reaction_id,
                                                                  "Rank": str(rank), "IsActive": "true"})
        native_name = next((name for name, tag in ((node.findtext("Name"), node.findtext("Tag"))
                                                   for node in root.findall("./GraphicObjects/GraphicObject"))
                            if tag == unit["tag"]), None)
        sim = simulations.get(native_name or "")
        if sim is None:
            raise MaterializationError("reaction_unit_missing", f"PFR {unit['tag']} is missing from the saved case")
        _child(sim, "ReactionSetID").text = set_id
    def stream_info(kind: str, stream_id: str, behavior: str, stream_type: str, stage: str | None) -> ElementTree.Element:
        item = ElementTree.Element(kind, {"ID": stream_id})
        def sub(parent: ElementTree.Element, name: str, value: str | None = None) -> ElementTree.Element:
            child = ElementTree.SubElement(parent, name)
            child.text = value
            return child
        sub(item, "Type", "DWSIM.UnitOperations.UnitOperations.Auxiliary.SepOps.StreamInformation")
        sub(item, "StreamID", stream_id)
        flow = sub(item, "FlowRate")
        sub(flow, "Type", "DWSIM.UnitOperations.UnitOperations.Auxiliary.SepOps.Parameter")
        for key, value in (("MaxVal", "0"), ("MinVal", "0"), ("Value", "0"), ("ParamType", "Fixed")):
            sub(flow, key, value)
        sub(item, "ID", stream_id)
        sub(item, "SideOpID")
        sub(item, "StreamPhase", "L")
        sub(item, "StreamBehavior", behavior)
        sub(item, "StreamType", stream_type)
        if stream_type == "Material":
            sub(item, "StreamPosition", "Above")
        if stage is not None:
            sub(item, "AssociatedStage", stage)
        return item

    for unit in (item for item in _units(document) if item["type"] == "DistillationColumn"):
        graph = graphics[unit["tag"]]
        native_name = native_by_tag[unit["tag"]]
        node = simulations[native_name]
        props = _unit_properties(unit)
        count = int(props["NumberOfStages"])
        stages = node.find("Stages")
        if stages is None or len(stages) < 2:
            raise MaterializationError("column_native_shape", "DWSIM column stage template is unavailable")
        def resize(container: ElementTree.Element, size: int = count) -> None:
            while len(container) < size:
                container.insert(len(container) - 1, copy.deepcopy(container[1]))
            while len(container) > size:
                container.remove(container[len(container) - 2])
        resize(stages)
        estimates = node.find("InitialEstimates")
        if estimates is not None:
            for estimate in estimates:
                if len(estimate):
                    resize(estimate)
        stage_ids = []
        for index, stage in enumerate(stages):
            stage_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{native_name}/stage/{index}"))
            _child(stage, "ID").text = stage_id
            _child(stage, "Name").text = f"Stage{index + 1}" + (" (Condenser)" if index == 0 else " (Reboiler)" if index == count - 1 else "")
            stage_ids.append(stage_id)
            pressure_key = "__TopPressure" if index == 0 else "__BottomPressure" if index == count - 1 else None
            if pressure_key:
                _child(stage, "P").text = repr(float(props[pressure_key]))
        for name in ("MaterialStreams", "EnergyStreams"):
            container = node.find(name)
            if container is None:
                container = ElementTree.SubElement(node, name)
            container.clear()
        for spec_id, key in (("C", "__CondenserSpec"), ("R", "__ReboilerSpec")):
            spec_node = node.find(f"./Specs/Spec[@ID='{spec_id}']")
            if spec_node is None:
                raise MaterializationError("column_spec_template_missing", "DWSIM column specification template is unavailable")
            _child(spec_node, "SpecValue").text = repr(float(props[key]))
        feed_stage = max(0, min(count - 1, int(props["__FeedStage"])))
        material = _child(node, "MaterialStreams")
        energy = _child(node, "EnergyStreams")
        for stream in _streams(document):
            if stream["target"] and stream["target"]["unit"] == unit["id"] and stream["type"] != "EnergyStream":
                material.append(stream_info("MaterialStream", native_by_tag[stream["tag"]], "Feed", "Material", stage_ids[feed_stage]))
            elif stream["source"] and stream["source"]["unit"] == unit["id"] and stream["type"] != "EnergyStream":
                port = stream["source"]["port"]
                behavior, stage_id = (("Distillate", stage_ids[0]) if port == 0 else ("BottomsLiquid", stage_ids[-1]))
                material.append(stream_info("MaterialStream", native_by_tag[stream["tag"]], behavior, "Material", stage_id))
            if stream["target"] and stream["target"]["unit"] == unit["id"] and stream["type"] == "EnergyStream":
                energy.append(stream_info("EnergyStream", native_by_tag[stream["tag"]], "BottomsLiquid", "Energy", None))
                _attach_column(_child(graph, "InputConnectors")[10], native_by_tag[stream["tag"]], 0, "input", "unit")
                _attach_column(_child(graphics[stream["tag"]], "OutputConnectors")[0], native_name, 10,
                               "output", "stream")
            elif stream["source"] and stream["source"]["unit"] == unit["id"] and stream["type"] == "EnergyStream":
                energy.append(stream_info("EnergyStream", native_by_tag[stream["tag"]], "Distillate", "Energy", None))
                _attach_column(_child(graph, "OutputConnectors")[10], native_by_tag[stream["tag"]], 0, "output", "unit")
                _attach_column(_child(graphics[stream["tag"]], "InputConnectors")[0], native_name, 10,
                               "input", "stream")
    tree.write(case_path, encoding="utf-8", xml_declaration=True)


def _attach_column(connector: ElementTree.Element, other_id: str, other_index: int, direction: str,
                   side: str) -> None:
    """Write the native column connectors using DWSIM's stream-side connection flags."""
    connector.attrib.clear()
    if side == "unit":
        connector.attrib.update(IsAttached="true", ConnType="ConEn",
                                **({"AttachedFromObjID": other_id, "AttachedFromConnIndex": str(other_index),
                                    "AttachedFromEnergyConn": "True"} if direction == "input" else
                                   {"AttachedToObjID": other_id, "AttachedToConnIndex": str(other_index),
                                    "AttachedToEnergyConn": "True"}))
    else:
        connector.attrib.update(IsAttached="true", ConnType="ConIn" if direction == "input" else "ConOut",
                                **({"AttachedFromObjID": other_id, "AttachedFromConnIndex": str(other_index),
                                    "AttachedFromEnergyConn": "False"} if direction == "input" else
                                   {"AttachedToObjID": other_id, "AttachedToConnIndex": str(other_index),
                                    "AttachedToEnergyConn": "False"}))


def expected(document: dict[str, Any]) -> dict[str, Any]:
    """The normalized materialization the compiler must produce for this draft document."""
    by_id = document["objects"]
    connections = []
    for stream in _streams(document):
        if stream["target"]:
            target = by_id[stream["target"]["unit"]]
            native_port = _native_energy_port(target, stream["target"]["port"]) if stream["type"] == "EnergyStream" else stream["target"]["port"]
            connections.append(f"{stream['tag']}>{target['tag']}:in{native_port}")
        if stream["source"]:
            source = by_id[stream["source"]["unit"]]
            native_port = _native_energy_port(source, stream["source"]["port"]) if stream["type"] == "EnergyStream" else stream["source"]["port"]
            connections.append(f"{source['tag']}:out{native_port}>{stream['tag']}")
    return {
        "compounds": sorted(document["compounds"]),
        "property_package": document["property_package"],
        "objects": {item["tag"]: {"type": item["type"], "x": item["x"], "y": item["y"]}
                    for item in document["objects"].values()},
        "connections": sorted(connections),
        "feeds": {stream["tag"]: _feed_expected(document, stream)
                  for stream in _material_streams(document) if stream["source"] is None},
        "energy_streams": {stream["tag"]: ({"EnergyFlow": float(stream["spec"]["duty"]["si"])}
                                           if "duty" in stream["spec"] else {})
                           for stream in _energy_streams(document)},
        "reactions": {reaction_id: {
            "name": reaction["name"], "stoichiometry": reaction["stoichiometry"],
            "orders": {compound: float(reaction["orders"].get(
                compound, 1.0 if compound == reaction["base_reactant"] else 0.0))
                       for compound in reaction["stoichiometry"]},
            "base_reactant": reaction["base_reactant"], "phase": reaction["phase"],
            "basis": reaction["basis"], "A_forward": float(reaction["A_forward"]["value"]),
            "A_forward_unit": reaction["A_forward"]["unit"],
            "E_forward": float(reaction["E_forward"]["value"]),
            "E_forward_unit": reaction["E_forward"]["unit"],
        } for reaction_id, reaction in document.get("reactions", {}).items()},
        "reaction_sets": {f"JARVIS_{unit['tag']}": list(unit["reactions"])
                          for unit in _units(document) if unit["type"] == "PFR" and unit.get("reactions")},
        "units": {unit["tag"]: _unit_properties(unit) for unit in _units(document)},
    }


def plan(document: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Exact ordered MCP calls (without the flowsheet handle) that materialize the draft."""
    calls: list[tuple[str, dict[str, Any]]] = [
        ("dwsim_thermo_add_compounds", {"names": list(document["compounds"])}),
        ("dwsim_thermo_set_property_package", {"name": document["property_package"]}),
    ]
    for stream in _streams(document):
        args: dict[str, Any] = {"name": stream["tag"]}
        if stream["type"] == "EnergyStream":
            calls.append(("dwsim_stream_add_energy", args))
        elif stream["source"] is None:
            calls.extend(_feed_calls(document, stream))
        else:
            calls.append(("dwsim_stream_add_material", args))
    for unit in _units(document):
        calls.append(("dwsim_unitop_add", {"type": UNIT_REGISTRY[unit["type"]].dwsim_type, "name": unit["tag"]}))
    for item in sorted(document["objects"].values(), key=lambda value: value["tag"]):
        calls.append(("dwsim_graphic_edit", {"name": item["tag"], "x": item["x"], "y": item["y"]}))
    by_id = document["objects"]
    for stream in _streams(document):
        if stream["target"]:
            unit = by_id[stream["target"]["unit"]]
            energy = stream["type"] == "EnergyStream"
            if energy and unit["type"] == "DistillationColumn":
                continue
            calls.append(("dwsim_unitop_connect", {"unitop": unit["tag"],
                         "energy_feed" if energy else "feed_stream": stream["tag"],
                         "energy_feed_port" if energy else "feed_port": _native_energy_port(unit, stream["target"]["port"]) if energy else stream["target"]["port"]}))
        if stream["source"]:
            unit = by_id[stream["source"]["unit"]]
            energy = stream["type"] == "EnergyStream"
            if energy and unit["type"] == "DistillationColumn":
                continue
            calls.append(("dwsim_unitop_connect", {"unitop": unit["tag"],
                         "energy_product" if energy else "product_stream": stream["tag"],
                         "energy_product_port" if energy else "product_port": _native_energy_port(unit, stream["source"]["port"]) if energy else stream["source"]["port"]}))
    for unit in _units(document):
        properties = _unit_properties(unit)
        if properties:
            if unit["type"] == "DistillationColumn":
                properties["Condenser_Specification_Value"] = properties["__CondenserSpec"]
                properties["Reboiler_Specification_Value"] = properties["__ReboilerSpec"]
            if unit["type"] == "Splitter" and "__SplitRatio1" in properties:  # flow-spec modes carry no ratios
                properties["SR1"] = properties["__SplitRatio1"]
                outlet_count = sum(1 for stream in _streams(document)
                                   if stream["source"] and stream["source"]["unit"] == unit["id"])
                if outlet_count == 3:
                    properties["SR2"] = properties["__SplitRatio2"]
            properties = {key: value for key, value in properties.items() if not key.startswith("__")}
            calls.append(("dwsim_unitop_set", {"name": unit["tag"], "properties": properties}))
    for stream in _energy_streams(document):
        if "duty" in stream["spec"]:
            calls.append(("dwsim_unitop_set", {"name": stream["tag"],
                                                "properties": {"EnergyFlow": float(stream["spec"]["duty"]["si"])}}))
    return calls


def _xml_root(path: Path) -> ElementTree.Element:
    import zipfile

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            name = next(item for item in archive.namelist() if item.lower().endswith(".xml"))
            return ElementTree.fromstring(archive.read(name))
    return ElementTree.parse(path).getroot()


def _float(text: str | None) -> float | str | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return text


def read_back(client: DwsimMcpClient, flow: str, case_path: Path, exp: dict[str, Any]) -> dict[str, Any]:
    """Normalized materialization as DWSIM actually holds it (live MCP + saved native case)."""
    root = _xml_root(case_path)
    native_types = {node.findtext("ComponentName"): (node.findtext("Type") or "").rsplit(".", 1)[-1]
                    for node in root.findall("./SimulationObjects/SimulationObject")}
    sim_nodes = {node.findtext("ComponentName"): node for node in root.findall("./SimulationObjects/SimulationObject")}
    tags: dict[str, str] = {}
    objects: dict[str, Any] = {}
    for node in root.findall("./GraphicObjects/GraphicObject"):
        native_id, tag = node.findtext("Name"), node.findtext("Tag")
        if not native_id or native_id not in native_types or not tag:
            continue
        tags[native_id] = tag
        native = native_types[native_id]
        objects[tag] = {"type": _NATIVE_TO_TYPE.get(native, native), "x": round(float(node.findtext("X") or 0)),
                        "y": round(float(node.findtext("Y") or 0))}
    # Native connectors: a unit input names its stream in AttachedFromObjID, an output in AttachedToObjID.
    # Both the unit side and the stream side are read; a one-sided attachment is itself a mismatch.
    unit_side: set[str] = set()
    stream_side: set[str] = set()
    for node in root.findall("./GraphicObjects/GraphicObject"):
        tag = tags.get(node.findtext("Name") or "")
        if tag is None:
            continue
        is_stream = objects[tag]["type"] in {"MaterialStream", "EnergyStream"}
        for direction in ("Input", "Output"):
            for index, conn in enumerate(node.findall(f"./{direction}Connectors/Connector")):
                if conn.get("IsAttached", "false").lower() != "true":
                    continue
                other_id = conn.get("AttachedFromObjID") if direction == "Input" else conn.get("AttachedToObjID")
                other = tags.get(other_id or "", "?")
                other_port = conn.get("AttachedFromConnIndex") if direction == "Input" else conn.get("AttachedToConnIndex")
                if not is_stream:
                    unit_side.add(f"{other}>{tag}:in{index}" if direction == "Input" else f"{tag}:out{index}>{other}")
                elif direction == "Input":
                    stream_side.add(f"{other}:out{other_port}>{tag}")
                else:
                    stream_side.add(f"{tag}>{other}:in{other_port}")
    if not tags:
        raise MaterializationError("connector_readback_unavailable", "Saved DWSIM case has no graphic objects")
    connections = sorted(unit_side | stream_side | {f"one-sided:{item}" for item in unit_side ^ stream_side})
    package_node = root.find("./PropertyPackages/PropertyPackage")
    package = None if package_node is None else (package_node.findtext("ComponentName") or package_node.findtext("Tag"))
    compounds = sorted(name.text for name in root.findall("./Compounds/Compound/Name") if name.text)
    feeds: dict[str, Any] = {}
    native_by_tag = {tag: native_id for native_id, tag in tags.items()}
    for tag, wanted in exp["feeds"].items():
        if tag not in objects:
            continue
        result = client.call("dwsim_stream_get_results", {"flowsheet_id": flow, "name": tag}, 30)
        phases = {phase.get("name"): phase for phase in result.get("phases", []) if isinstance(phase, dict)}
        mixture = sorted((phases.get("Mixture", {}).get("compounds") or {}).items())
        sim_node = sim_nodes.get(native_by_tag[tag])
        held: dict[str, Any] = {
            **{arg: result.get(arg) for _key, (_kind, arg, _label) in STREAM_SPECS.items() if arg != "vapor_fraction"},
            "vapor_fraction": phases.get("Vapor", {}).get("fraction"),
            "spec_type": sim_node.findtext("SpecType") if sim_node is not None else None,
            "defined_flow": sim_node.findtext("DefinedFlow") if sim_node is not None else None,
            "composition": {name: value.get("mass_fraction") for name, value in mixture},
            "mole_composition": {name: value.get("mole_fraction") for name, value in mixture},
        }
        # Only the chosen alternatives are compared; the others are DWSIM-calculated, not inputs.
        feeds[tag] = {key: held[key] for key in wanted}
    units: dict[str, Any] = {}
    for native_id, tag in tags.items():
        if objects[tag]["type"] in UNIT_REGISTRY:
            wanted = exp["units"].get(tag) or {}
            node = sim_nodes[native_id]
            if objects[tag]["type"] == "DistillationColumn":
                stages = node.find("Stages")
                stage_ids = [stage.findtext("ID") for stage in stages or []]
                values = {"__FeedStage": next((stage_ids.index(item.findtext("AssociatedStage"))
                                                    for item in node.findall("./MaterialStreams/MaterialStream")
                                                    if item.findtext("StreamBehavior") == "Feed"), None),
                          "__TopPressure": _float(stages[0].findtext("P")) if stages is not None and len(stages) else None,
                          "__BottomPressure": _float(stages[-1].findtext("P")) if stages is not None and len(stages) else None}
                for spec_id, key in (("C", "__CondenserSpec"), ("R", "__ReboilerSpec")):
                    spec_node = node.find(f"./Specs/Spec[@ID='{spec_id}']")
                    values[key] = _float(spec_node.findtext("SpecValue")) if spec_node is not None else None
                units[tag] = {name: values.get(name, _float(node.findtext(name))) for name in wanted}
            elif objects[tag]["type"] == "PFR":
                units[tag] = {name: (node.findtext("ReactionSetID") if name == "__ReactionSetID"
                                     else _float(node.findtext(name)) if name != "CalcMode" else node.findtext(name))
                              for name in wanted}
            elif objects[tag]["type"] == "Splitter":
                ratios = [_float(item.text) for item in node.findall("./SplitRatios/SplitRatio")]
                units[tag] = {}
                for name in wanted:
                    if name.startswith("__SplitRatio"):
                        index = int(name[-1]) - 1
                        units[tag][name] = ratios[index] if index < len(ratios) else None
                    elif name == "OperationMode":
                        units[tag][name] = node.findtext(name)
                    else:
                        units[tag][name] = _float(node.findtext(name))
            elif objects[tag]["type"] == "HeatExchanger":
                units[tag] = {name: (node.findtext("CalculationMode") if name == "CalculationMode"
                                     else _float(node.findtext(name))) for name in wanted}
            else:
                units[tag] = {name: _float(node.findtext(name)) if name != "CalcMode" else node.findtext(name)
                              for name in wanted}
    energy_streams = {}
    for tag, wanted in exp.get("energy_streams", {}).items():
        energy_node = sim_nodes.get(next((native for native, native_tag in tags.items() if native_tag == tag), ""))
        energy_streams[tag] = {key: _float(energy_node.findtext(key)) if energy_node is not None else None
                               for key in wanted}
    reactions = {}
    for reaction_id in exp.get("reactions", {}):
        reaction = root.find(f"./Reactions/Reaction[ID='{reaction_id}']")
        compounds_node = None if reaction is None else reaction.find("Compounds")
        reaction_compounds = list(compounds_node or [])
        reactions[reaction_id] = {
            "name": reaction.findtext("Name") if reaction is not None else None,
            "stoichiometry": {item.get("Name"): _float(item.get("StoichCoeff")) for item in reaction_compounds},
            "orders": {item.get("Name"): _float(item.get("DirectOrder")) for item in reaction_compounds},
            "base_reactant": reaction.findtext("BaseReactant") if reaction is not None else None,
            "phase": reaction.findtext("ReactionPhase") if reaction is not None else None,
            "basis": reaction.findtext("ReactionBasis") if reaction is not None else None,
            "A_forward": _float(reaction.findtext("A_Forward")) if reaction is not None else None,
            "A_forward_unit": reaction.findtext("VelUnit") if reaction is not None else None,
            "E_forward": _float(reaction.findtext("E_Forward")) if reaction is not None else None,
            "E_forward_unit": reaction.findtext("E_Forward_Unit") if reaction is not None else None,
        }
    reaction_sets = {}
    for reaction_set_id in exp.get("reaction_sets", {}):
        reaction_set = root.find(f"./ReactionSets/ReactionSet[ID='{reaction_set_id}']")
        reaction_sets[reaction_set_id] = [item.get("ReactionID") or item.get("Key")
                                          for item in (reaction_set.findall("./Reactions/Reaction")
                                                       if reaction_set is not None else [])]
    return {"compounds": compounds, "property_package": package, "objects": objects,
            "connections": sorted(connections), "feeds": feeds,
            "energy_streams": energy_streams, "reactions": reactions,
            "reaction_sets": reaction_sets, "units": units}


def _same(actual: Any, wanted: Any) -> bool:
    if isinstance(wanted, float) or isinstance(actual, float):
        try:
            return math.isclose(float(actual), float(wanted), rel_tol=_REL_TOL, abs_tol=_ABS_TOL)
        except (TypeError, ValueError):
            return False
    return actual == wanted


def compare(exp: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    """Field-by-field differences between expected and read-back materializations."""
    diffs: list[dict[str, Any]] = []

    def walk(path: str, wanted: Any, got: Any) -> None:
        if isinstance(wanted, dict) and isinstance(got, dict):
            for key in sorted(set(wanted) | set(got), key=str):
                if key not in got:
                    diffs.append({"path": f"{path}.{key}", "expected": wanted[key], "actual": "<missing>"})
                elif key not in wanted:
                    diffs.append({"path": f"{path}.{key}", "expected": "<absent>", "actual": got[key]})
                else:
                    walk(f"{path}.{key}", wanted[key], got[key])
        elif isinstance(wanted, list) and isinstance(got, list):
            for item in sorted(set(map(str, wanted)) - set(map(str, got))):
                diffs.append({"path": f"{path}[{item}]", "expected": item, "actual": "<missing>"})
            for item in sorted(set(map(str, got)) - set(map(str, wanted))):
                diffs.append({"path": f"{path}[{item}]", "expected": "<absent>", "actual": item})
        elif not _same(got, wanted):
            diffs.append({"path": path, "expected": wanted, "actual": got})

    for section in ("compounds", "property_package", "objects", "connections", "feeds", "energy_streams",
                    "reactions", "reaction_sets", "units"):
        walk(section, exp[section], actual.get(section))
    return diffs


def _stable(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".9g")
    if isinstance(value, dict):
        return {str(key): _stable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def process_view(normalized: dict[str, Any]) -> dict[str, Any]:
    """The materialization without layout: object positions never change process meaning."""
    view = copy.deepcopy(normalized)
    view["objects"] = {tag: {"type": item["type"]} for tag, item in normalized["objects"].items()}
    return view


def fingerprint(normalized: dict[str, Any], *, dwsim_version: str, mcp_sha256: str) -> str:
    payload = {"compiler_version": COMPILER_VERSION, "dwsim_version": dwsim_version, "mcp_sha256": mcp_sha256,
               "materialization": _stable(normalized)}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def result_fingerprint(document: dict[str, Any], *, dwsim_version: str, mcp_sha256: str) -> str:
    """Jarvis result identity includes culture while DWSIM materialization remains untouched."""
    from app.modules.process_stack.culture import PROPAGATION_VERSION, RESULT_SCHEMA_VERSION

    dwsim_process = fingerprint(process_view(expected(document)), dwsim_version=dwsim_version,
                                mcp_sha256=mcp_sha256)
    culture = {item["tag"]: item.get("spec", {}).get("culture")
               for item in document["objects"].values()
               if item["kind"] == "stream" and item.get("spec", {}).get("culture") is not None}
    payload = {"dwsim_process_fingerprint": dwsim_process, "culture": culture,
               "culture_schema_version": RESULT_SCHEMA_VERSION,
               "culture_propagation_version": PROPAGATION_VERSION}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _stream_result(result: dict[str, Any]) -> dict[str, Any]:
    phases = {phase.get("name"): phase for phase in result.get("phases", []) if isinstance(phase, dict)}
    mixture = phases.get("Mixture", {})
    return {
        # Preserve the complete DWSIM response as the authoritative result catalogue. The
        # normalized fields below remain a convenience projection; none are recomputed.
        "reported": result,
        "temperature_K": result.get("temperature_K"),
        "pressure_Pa": result.get("pressure_Pa"),
        "mass_flow_kg_s": result.get("mass_flow_kg_s"),
        "molar_flow_mol_s": result.get("molar_flow_mol_s"),
        "vapor_fraction": phases.get("Vapor", {}).get("fraction"),
        "mass_fractions": {name: value.get("mass_fraction")
                           for name, value in sorted((mixture.get("compounds") or {}).items())},
    }


def _property_group(name: str) -> str:
    key = name.casefold()
    if any(term in key for term in ("temperature", "pressure", "mass flow", "molar flow", "volume flow", "enthalpy flow")):
        return "conditions"
    if any(term in key for term in ("phase", "vapor fraction", "liquid fraction")):
        return "phases"
    if any(term in key for term in ("fraction", "compound flow", "composition")):
        return "composition"
    if any(term in key for term in ("viscosity", "conductivity", "diffusivity", "diffusion", "reynolds", "prandtl")):
        return "transport"
    if any(term in key for term in ("fugacity", "activity", "bubble point", "dew point", "equilibrium")):
        return "equilibrium"
    if any(term in key for term in ("enthalpy", "entropy", "heat capacity", "cp", "cv", "compressibility", "gibbs", "helmholtz", "density")):
        return "thermodynamic"
    return "other"


def _snapshot_properties(rows: list[dict[str, Any]], tag: str) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row.get("object") != tag:
            continue
        value = row.get("b")
        if isinstance(value, float) and not math.isfinite(value):
            value = None
        name = str(row.get("property") or row.get("id") or "")
        result.append({"id": row.get("id", ""), "name": name, "group": _property_group(name),
                       "unit": row.get("unit", ""), "value": value,
                       "specification": bool(row.get("specification", False))})
    return sorted(result, key=lambda item: (item["group"], item["name"], item["id"]))


def materialize(document: dict[str, Any], *, action: str, client: DwsimMcpClient, dwsim_version: str,
                mcp_sha256: str, label: str, keep_case: Path | None = None) -> dict[str, Any]:
    """Compile, read back, compare; then check (validate) or check+solve (run). Refuses on mismatch."""
    started = time.perf_counter()
    exp = expected(document)
    outcome: dict[str, Any] = {"expected_fingerprint": fingerprint(exp, dwsim_version=dwsim_version,
                                                                   mcp_sha256=mcp_sha256)}
    with tempfile.TemporaryDirectory(prefix="jarvis-draft-") as tmp:
        case = Path(tmp) / "materialized.dwxml"
        step = "dwsim_flowsheet_create"
        try:
            created = client.call("dwsim_flowsheet_create", {"name": label}, 30)
            flow = created.get("flowsheet_id")
            if not isinstance(flow, str):
                raise MaterializationError("materialization_failed", "DWSIM did not create a flowsheet")
            for step, args in plan(document):
                client.call(step, {"flowsheet_id": flow, **args}, 60)
            step = "dwsim_flowsheet_save"
            client.call("dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(case), "compressed": False}, 60)
            native_patch_required = any(unit["type"] == "DistillationColumn" or
                                        unit["type"] == "PFR" and unit.get("reactions")
                                        for unit in _units(document))
            if native_patch_required:
                step = "column_native_patch"
                _patch_native_xml(case, document)
                step = "column_reload"
                reloaded = client.call("dwsim_flowsheet_load", {"filepath": str(case)}, 60)
                flow = reloaded.get("flowsheet_id")
                if not isinstance(flow, str):
                    raise MaterializationError("column_reload_failed", "DWSIM did not reload the patched column case")
                for unit in _units(document):
                    if unit["type"] == "PFR" and unit.get("reactions"):
                        client.call("dwsim_unitop_set", {"flowsheet_id": flow, "name": unit["tag"],
                                                          "properties": {"ReactionSetID": f"JARVIS_{unit['tag']}"}}, 60)
            step = "read_back"
            actual = read_back(client, flow, case, exp)
        except DwsimMcpError as exc:
            raise MaterializationError("materialization_failed", f"DWSIM refused {step}",
                                       step=step, dwsim_code=getattr(exc, "code", None),
                                       dwsim_message=str(exc)[:600]) from exc
        diffs = compare(exp, actual)
        outcome.update(materialization_fingerprint=fingerprint(actual, dwsim_version=dwsim_version,
                                                                mcp_sha256=mcp_sha256),
                       materialization_diffs=diffs, materialized_object_count=len(actual["objects"]))
        if not diffs:
            # The read-back equals ``exp`` field by field, so the layout-free fingerprint of ``exp`` is
            # the verified process meaning that later layout-only revisions are compared against.
            outcome["process_fingerprint"] = fingerprint(process_view(exp), dwsim_version=dwsim_version,
                                                         mcp_sha256=mcp_sha256)
        if diffs:
            outcome.update(status="materialization_mismatch", compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        check = client.call("dwsim_flowsheet_check", {"flowsheet_id": flow}, 30)
        outcome["dwsim_check"] = {
            "ready": check.get("ready"),
            "findings": [{"severity": item.get("severity"), "code": item.get("code"), "object": item.get("object"),
                          "message": item.get("message"), "fix": item.get("fix"), "source": "dwsim"}
                         for item in check.get("findings", []) if isinstance(item, dict)][:40],
        }
        if action == "validate":
            outcome.update(status="validated" if check.get("ready") else "check_failed",
                           compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        if not check.get("ready"):
            outcome.update(status="check_failed", compile_seconds=round(time.perf_counter() - started, 3))
            return outcome
        solve = client.call("dwsim_solve_run", {"flowsheet_id": flow, "timeout_s": 120}, 150)
        snapshot_rows: list[dict[str, Any]] = []
        if solve.get("ok") is True:
            client.call("dwsim_scenario_snapshot", {"flowsheet_id": flow, "label": "jarvis_result"}, 60)
            catalogue = client.call("dwsim_scenario_compare", {"flowsheet_id": flow, "label_a": "jarvis_result",
                                     "label_b": "jarvis_result", "only_changed": False, "limit": 20000}, 90)
            snapshot_rows = [row for row in catalogue.get("rows", []) if isinstance(row, dict)]
        solved_case = Path(tmp) / "solved.dwxmz"
        client.call("dwsim_flowsheet_save", {"flowsheet_id": flow, "filepath": str(solved_case), "compressed": True}, 60)
        listed = client.call("dwsim_flowsheet_list_objects", {"flowsheet_id": flow}, 30).get("objects", [])
        object_status = [{"tag": item.get("name"), "calculated": item.get("calculated"), "error": item.get("error", "")}
                         for item in listed if isinstance(item, dict)]
        streams = {stream["tag"]: {**_stream_result(client.call("dwsim_stream_get_results",
                                    {"flowsheet_id": flow, "name": stream["tag"]}, 30)),
                                    "properties": _snapshot_properties(snapshot_rows, stream["tag"])}
                   for stream in _material_streams(document)}
        energy_results = {stream["tag"]: client.call("dwsim_unitop_get_results",
                                                       {"flowsheet_id": flow, "name": stream["tag"]}, 30)
                          for stream in _energy_streams(document)}
        for tag, result in energy_results.items():
            result["properties"] = _snapshot_properties(snapshot_rows, tag)
        units = {}
        for unit in _units(document):
            reported = client.call("dwsim_unitop_get_results", {"flowsheet_id": flow, "name": unit["tag"]}, 30)
            units[unit["tag"]] = {"calculated": reported.get("calculated"), "error": reported.get("error", ""),
                                  "reported": reported.get("properties", {}),
                                  "properties": _snapshot_properties(snapshot_rows, unit["tag"])}
        try:
            tagged = [{**item, "tag": item.get("name")} for item in listed if isinstance(item, dict)]
            residual, boundary = _mass_balance(client, flow, solved_case, tagged)
            balance = {"status": "calculated", "residual_kg_s": residual, "boundary_kg_s": boundary}
        except Exception as exc:  # noqa: BLE001 - balance is reported, never invented
            balance = {"status": "unavailable", "error": getattr(exc, "code", type(exc).__name__)}
        errors = solve.get("errors") if isinstance(solve.get("errors"), list) else []
        failed = [item for item in object_status if item["calculated"] is False or item["error"]]
        outcome.update(
            status="completed" if solve.get("ok") is True and not errors and not failed else "failed",
            solve={"ok": solve.get("ok"), "errors": errors[:20], "failed_objects": failed[:20]},
            streams=streams, energy_streams=energy_results, units=units, mass_balance=balance,
            solved_case_sha256=hashlib.sha256(solved_case.read_bytes()).hexdigest(),
            compile_seconds=round(time.perf_counter() - started, 3),
        )
        if keep_case is not None:
            keep_case.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(solved_case, keep_case)
    return outcome


def new_run_id() -> str:
    return uuid4().hex
