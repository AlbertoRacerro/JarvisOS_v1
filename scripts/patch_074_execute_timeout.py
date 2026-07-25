from pathlib import Path

PATH = Path("backend/app/modules/bluecad/cad_link_topology_execute.py")
text = PATH.read_text(encoding="utf-8")
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
PATH.write_text(text, encoding="utf-8")
