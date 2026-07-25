from pathlib import Path

EXECUTE = Path("backend/app/modules/bluecad/cad_link_topology_execute.py")
text = EXECUTE.read_text(encoding="utf-8")
old_import = '''from app.modules.bluecad.cad_link_topology import (
    CadLink072ExecuteRequest,
'''
new_import = '''from app.modules.bluecad.cad_link_topology import (
    BUILD_TIMEOUT_SECONDS,
    CadLink072ExecuteRequest,
'''
if text.count(old_import) != 1:
    raise SystemExit("execute topology import target missing")
text = text.replace(old_import, new_import, 1)
old_call = '        result = build_geometry_spec(preview["resolved_spec"], out_dir)\n'
new_call = '''        result = build_geometry_spec(
            preview["resolved_spec"],
            out_dir,
            timeout_s=BUILD_TIMEOUT_SECONDS,
        )
'''
if text.count(old_call) != 1:
    raise SystemExit("execute build call target missing")
text = text.replace(old_call, new_call, 1)
EXECUTE.write_text(text, encoding="utf-8")

TOPOLOGY = Path("backend/app/modules/bluecad/cad_link_topology.py")
topology = TOPOLOGY.read_text(encoding="utf-8")
if topology.count("BUILD_TIMEOUT_SECONDS = 120.0") != 1:
    raise SystemExit("topology build timeout target missing")
topology = topology.replace(
    "BUILD_TIMEOUT_SECONDS = 120.0",
    "BUILD_TIMEOUT_SECONDS = 35.0",
    1,
)
TOPOLOGY.write_text(topology, encoding="utf-8")

EXPORT = Path("backend/app/modules/bluecad/export.py")
export = EXPORT.read_text(encoding="utf-8")
replacements = (
    (
        "    out_path.mkdir(parents=True, exist_ok=True)\n    parts = assemble_parts(spec)\n",
        "    out_path.mkdir(parents=True, exist_ok=True)\n"
        "    (out_path / '.bluecad_build_phase').write_text('assemble', encoding='utf-8')\n"
        "    parts = assemble_parts(spec)\n"
        "    (out_path / '.bluecad_build_phase').write_text('step', encoding='utf-8')\n",
        "assemble phase",
    ),
    (
        "    _normalize_step_header_timestamp(step_path)\n    bd.export_stl(shape, out_dir / \"model.stl\")\n",
        "    _normalize_step_header_timestamp(step_path)\n"
        "    (out_dir / '.bluecad_build_phase').write_text('stl', encoding='utf-8')\n"
        "    bd.export_stl(shape, out_dir / \"model.stl\")\n",
        "stl phase",
    ),
    (
        "    bd.export_gltf(shape, out_dir / \"model.glb\", binary=True, linear_deflection=0.001, angular_deflection=0.1)\n",
        "    (out_dir / '.bluecad_build_phase').write_text('glb', encoding='utf-8')\n"
        "    bd.export_gltf(shape, out_dir / \"model.glb\", binary=True, linear_deflection=0.001, angular_deflection=0.1)\n"
        "    (out_dir / '.bluecad_build_phase').write_text('manifest', encoding='utf-8')\n",
        "glb phase",
    ),
)
for old, new, label in replacements:
    if export.count(old) != 1:
        raise SystemExit(f"{label} target missing")
    export = export.replace(old, new, 1)
EXPORT.write_text(export, encoding="utf-8")
