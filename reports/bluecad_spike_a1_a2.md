# BLUECAD A1/A2 spike

## Environment

- Command: `backend\.venv\Scripts\python.exe scripts\spikes\bluecad_spike_a1_a2.py`
- Python: `3.13.14`
- build123d: `0.11.1`
- OCP/OCCT wheel: `cadquery-ocp-novtk==7.9.3.1.1`
- OCP proxy wheel: `cadquery-ocp-proxy==7.9.3.1.1`
- `OCP` distribution name: `not installed`; `import OCP` works via `cadquery-ocp-novtk`
- trimesh: `not installed`; not needed because native GLB export worked

## A1 verdict

- Native GLB: yes
- API used: `build123d.export_gltf(shape, path, binary=True, linear_deflection=0.001, angular_deflection=0.1)`
- Path chosen: native build123d GLB export
- Fallback path in script: `trimesh.load_mesh(stl_path).export(file_type="glb")`; not executed
- STEP API: `build123d.export_step`
- STL API: `build123d.export_stl`

## A2 verdict

- B-rep validity API: `build123d.Shape.is_valid`
- B-rep validity API: `OCP.BRepCheck.BRepCheck_Analyzer(shape.wrapped).IsValid()`
- Watertight/manifold API: `build123d.Shape.is_manifold`
- Closed shell API: `OCP.BRep.BRep_Tool.IsClosed_s(shell.wrapped)`
- Result: sufficient for Tier 1 validity plus closed-shell/watertight checks on this spike geometry.

## Results

| case | computed volume mm3 | analytic volume mm3 | rel error | validity | manifold | shell closed | STEP/STL/GLB |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `hollow_cylinder` | `1332035.285122073255` | `1332035.285122072324` | `6.991726007695e-16` | true | true | `[true]` | true/true/native |
| `torus_bend_90` | `836942.453212377848` | `836942.453212377615` | `2.781919387172e-16` | true | true | `[true, true]` | true/true/native |

## Timings

- Build total: `0.185080 s`
- `hollow_cylinder`: checks `0.001520 s`; STEP `0.007160 s`; STL `0.008196 s`; GLB `0.006775 s`; export total `0.022131 s`
- `torus_bend_90`: checks `0.002395 s`; STEP `0.004594 s`; STL `0.078035 s`; GLB `0.008317 s`; export total `0.090946 s`

## Artifacts

- `reports/bluecad_spike_a1_a2_artifacts/hollow_cylinder.step` (`9294` bytes)
- `reports/bluecad_spike_a1_a2_artifacts/hollow_cylinder.stl` (`50484` bytes)
- `reports/bluecad_spike_a1_a2_artifacts/hollow_cylinder.glb` (`32468` bytes)
- `reports/bluecad_spike_a1_a2_artifacts/torus_bend_90.step` (`10203` bytes)
- `reports/bluecad_spike_a1_a2_artifacts/torus_bend_90.stl` (`881684` bytes)
- `reports/bluecad_spike_a1_a2_artifacts/torus_bend_90.glb` (`334364` bytes)

## Windows notes

- No Windows-specific build/export/check failure hit.
- `pip install build123d` selected Windows CPython 3.13 wheel `cadquery-ocp-novtk==7.9.3.1.1`.
