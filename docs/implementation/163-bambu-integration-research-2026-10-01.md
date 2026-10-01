# Bambu Lab ecosystem integration with JarvisOS / BLUECAD: research report

Date: 2026-10-01. Evidence comes from web sources fetched today plus a read of the JarvisOS repo at `master` (fc34a316). Claims marked **[unverified]** could not be confirmed from a primary source. The Bambu wiki (`wiki.bambulab.com`) returned HTTP 402 to automated fetches, so content from it is quoted only through search-result snippets.

## 0. Bottom line

Use **file handoff only**. JarvisOS owns design intent, geometry, units and validation. Bambu Studio owns orientation, supports, slicing, plate/filament settings and talking to the printer. The first step is a one-way "export print-ready mesh (3MF in mm, plus STL/STEP) and open it in Bambu Studio" action, triggered from WSL through the Windows file association. Do not handle printer access codes or cloud credentials, do not run MQTT/FTP, do not embed Bambu Studio, and do not call cloud APIs. A headless slicer CLI is a possible later, optional and isolated step. It is not needed now.

## 1. What Bambu Studio exposes today

- **License and lineage.** Bambu Studio is AGPL-3.0. It is derived from PrusaSlicer, which came from Slic3r ([GitHub README](https://github.com/bambulab/BambuStudio)). OrcaSlicer is a community fork of Bambu Studio and is also AGPL-3.0.
- **Proprietary parts.** The README says: "The bambu networking plugin is based on non-free libraries. It is optional to the Bambu Studio and provides extended networking functionalities." Cloud, device, MQTT-auth and camera features are in that closed plugin. Bambu Connect, Bambu Handy, printer firmware and Bambu Farm Manager are all proprietary. A GitHub issue from February 2025 says some Bambu Studio releases shipped with incomplete AGPL source. That issue is unresolved ([fusion94, 2026-05-26](https://fusion94.org/blog/2026-05-26-bambu-agpl/)) **[allegation, not adjudicated]**.
- **Current version.** Public release 2.8.2.61 (2026-08-21) and beta 2.8.4 ([MajorGeeks](https://www.majorgeeks.com/files/details/bambustudio.html), [GitHub releases](https://github.com/bambulab/BambuStudio/releases)). 2.6.1 (April 2026 beta) added a Filament Manager ([forum](https://forum.bambulab.com/t/bambu-studio-v2-6-1-public-beta-is-now-available/251485)). Check the exact build on the maintainer's machine.
- **Authorization control (January 2025 onward).** On 2025-01-16 Bambu announced firmware that requires authenticated control. X1 beta firmware 01.08.03.00 shipped 2025-01-17 ([Hackaday](https://hackaday.com/2025/01/17/new-bambu-lab-firmware-update-adds-mandatory-authorization-control-system/), [Rossmann wiki](https://wiki.rossmanngroup.com/wiki/Bambu_Lab_Authorization_Control_System)). Starting a print, motion, temperatures, AMS and firmware all need authorization through Bambu Studio, Bambu Connect or Handy. After backlash, Bambu's 2025-01-20 post ([blog](https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/)) kept an opt-in **Developer Mode** inside LAN-only mode. It gives open MQTT, live stream and FTP, "users assume full responsibility… no official support". Partnerships go through devpartner@bambulab.com.
- **Later developments.** In May 2025 Bambu sent a takedown for an "OrcaSlicer-BambuLab" fork and posted "Setting the Record Straight on Cloud Access" ([fusion94](https://fusion94.org/blog/2026-05-26-bambu-agpl/)). Commentators describe LAN and Developer Mode as "tolerated exceptions", not a stable contract. OrcaSlicer PR #15812 (opened 2026-09-22, still open) proposed a clean-room "Open Bambu Networking" plugin. Because of legal burden it was moved into an external plugin ([PR](https://github.com/OrcaSlicer/OrcaSlicer/pull/15812)). How it works (re-signing cloud commands) comes from a model summary of the PR. **[unverified detail; legally contested territory]**

## 2. File formats and workflows

- **3MF.** Bambu and Orca project 3MFs are ZIP files containing `3D/3dmodel.model` (core 3MF geometry, unit attribute), `Metadata/project_settings.config` (JSON of resolved printer, process and filament settings), `Metadata/model_settings.config` (XML plates, objects, per-object overrides), and after slicing `Metadata/plate_N.gcode`, `slice_info.config` and thumbnails ([Printago, 2026-04-13](https://printago.io/blog/3mf-file-format)). A sliced, print-ready file is a `.gcode.3mf`.
- **Can a third party produce a 3MF that opens with settings?** Yes in principle. It is plain ZIP/XML/JSON. But you must fill in `printer_model`, nozzle variant, filament arrays and plate layout so they match Bambu's internal schemas. Those schemas are undocumented and change between releases (`--uptodate` exists to migrate old 3MFs). **A plain core-spec 3MF (geometry and units only) opens reliably as an object import**, and the user then picks the printer and filament presets. That is the right target for JarvisOS. Writing Bambu settings metadata is fragile coupling.
- **STL** has no units. Bambu assumes mm. BLUECAD is mm-native (`bbox_mm`, `total_volume_mm3` in `spec.py`), so this works, but it should be stated explicitly.
- **STEP** import is supported. Bambu tessellates it using user-adjustable linear and angular deflection ([Bambu wiki STEP page](https://wiki.bambulab.com/en/software/bambu-studio/step), via snippet). Forum threads report import regressions across versions ([forum](https://forum.bambulab.com/t/bl-broke-step-import-in-v10/111994)). STEP keeps exact geometry, but meshing quality then depends on the slicer.

## 3. Interfaces

| Interface | What it is | Maturity / fit |
|---|---|---|
| **Bambu Studio CLI** | `bambu-studio --slice 0 --export-3mf out.3mf --load-settings m.json;p.json --load-filaments f.json --arrange 1 --orient in.stl` ([wiki](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage), [Printago flags](https://printago.io/slicer-cli/bambu)) | Works, used by Bambuddy and bambu-queue. Known problems: profiles must be **flattened** (inherits ignored), no thumbnails headless, output **not byte-deterministic**, metadata gaps ([3dprint4me PR #23](https://github.com/JerrettDavis/3dprint4me/pull/23)). Older Linux builds failed on GL init ([#6503](https://github.com/bambulab/BambuStudio/issues/6503)). Medium-low maturity. |
| **OrcaSlicer CLI** | Same Slic3r-lineage CLI | Similar caveats. Used for server-side slicing in Bambuddy ([docs](https://wiki.bambuddy.cool/features/slicer-api/)). |
| **URL schemes** | `bambustudio://open?file=`, `bambustudioopen://` | Client-side **domain allowlist** for Bambu/MakerWorld. Third-party URLs fail silently ([Production Shaped, 2026-05-14](https://productionshaped.com/notes/2026-05-14-bambu-studio-url-schemes-what-doesnt-work-and-why/)). Not usable. |
| **Bambu Connect** | `bambu-connect://import-file?path=<enc>&name=<enc>&version=1.0.0` ([forum announcement](https://forum.bambulab.com/t/updates-and-third-party-integration-with-bambu-connect/137408)) | Official third-party path, but it takes **already-sliced** `.gcode.3mf` files for printing. It does not slice. Only useful if JarvisOS ever slices. |
| **File association** | Double-click / `start file.3mf` opens Bambu Studio | Most robust option. No allowlist. From WSL: `cmd.exe /c start "" "$(wslpath -w file.3mf)"` or `explorer.exe`/`wslview`. |
| **LAN MQTT/FTPS** | MQTT TLS :8883, user `bblp` + access code, topics `device/{serial}/request|report`. Implicit FTPS :990 ([dev.to](https://dev.to/amsozzer/driving-a-bambu-lab-printer-over-mqtt-12nb), [bambuddy](https://wiki.bambuddy.cool/reference/troubleshooting/)) | Writes need LAN-only + Developer Mode, which turns cloud and Handy off. Unofficial and undocumented by Bambu. Bambu can break it with firmware. |
| **Cloud / Handy APIs** | Reverse-engineered only. No public API | Not an option. ToS and credential risk. |
| **SDK / plugins** | No official SDK. Partner program is by email. Orca has a community plugin system | Not usable for this project. |
| **Bambu Farm Manager** | Free Windows server+client, LAN, fleet queueing ([Tom's Hardware](https://www.tomshardware.com/3d-printing/bambu-lab-introduces-free-software-to-manage-an-unlimited-number-of-3d-printers-simultaneously-cloud-free-lan-mode-print-farm-manager-program-simplifies-mass-3d-printing)) | Overkill for one printer. No integration API. |

## 4. Consequences of each option

- **(a) File handoff (3MF/STL/STEP, opened in Bambu Studio).** License: none. JarvisOS writes open formats, and Bambu Studio runs as a separate program. Security: no credentials, no network, no printer control. Maintenance: very low. Core 3MF and STL are stable standards. Risk: the user has to pick presets by hand, which is the correct responsibility boundary anyway.
- **(b) Invoking the slicer CLI.** License: running an AGPL binary as a separate process is not linking, so no copyleft obligation unless you distribute a modified copy. Maintenance: medium-high. Flattened profiles drift with releases, output is not deterministic (clashes with JarvisOS's deterministic-artifact ethos, see `_normalize_step_header_timestamp` in export.py), headless GL quirks, and a large binary to pin. Security: low, if it is sandboxed with no network plugin.
- **(c) MQTT/FTP in Developer Mode.** License: none, but it is off-contract. Security: the access code is a long-lived LAN secret. JarvisOS would have to store it and could start physical actions (heaters, motion), so a software bug becomes a fire or hardware risk. Developer Mode disables cloud, Handy and remote features. Maintenance: high. Firmware can change or remove it at any time.
- **(d) Embedding Bambu Studio or its UI.** License: including or modifying AGPL code inside JarvisOS brings AGPL into the combined work. The UI is wxWidgets desktop and cannot be embedded in React in any reasonable way. The networking plugin is proprietary and cannot be redistributed. Do not do this.
- **(e) Cloud APIs.** No public API, ToS exposure, cloud account tokens to store, and the history above shows enforcement (takedown). Do not do this.

## 5. Current BLUECAD export state (repo evidence)

- `backend/app/modules/bluecad/export.py`: `ARTIFACT_NAMES = ("model.step", "model.stl", "model.glb")`. STEP comes from `bd.export_step` with a normalized timestamp, STL from `bd.export_stl(shape, …)` with build123d 0.11.1 defaults (`tolerance=0.001`, `angular_tolerance=0.1`, binary), and GLB from `bd.export_gltf` with scene-binding wrappers. **No 3MF export.** All parts are merged into one compound before STL, so per-part identity is lost.
- `backend/app/modules/bluecad/loop.py` (~L996-1035) **registers only** `bluecad_spec`, `bluecad_report`, `bluecad_manifest` and `bluecad_glb` as artifacts. `model.step` and `model.stl` are written to `out_dir` but **not registered or served**.
- `backend/app/modules/bluecad/routes.py`: `GET /artifacts/{artifact_id}/content` serves any registered `bluecad_*` artifact (special MIME only for GLB).
- Units are implicitly mm: `spec.py` (`bbox_mm`, `total_volume_mm3`) and `validate.py`.
- The installed build123d provides `Mesher(unit=Unit.MM)` with `add_shape(..., linear_deflection, angular_deflection, part_number=...)`, which can write **core 3MF with explicit mm units and one object per part**. That fits the deterministic per-part model.

What is missing for printing: (1) a print-oriented 3MF artifact with explicit units, (2) registering and serving STL/STEP/3MF, (3) a local "open in Bambu Studio" action.

## 6. Recommended architecture

```
BLUECAD spec -> build -> validate -> artifacts {step, stl, 3mf(mm, per-part objects), glb}
                                            |
                         JarvisOS UI "Download" / "Open in slicer"
                                            |
     backend (WSL) copies artifact to a Windows-visible handoff dir (e.g. /mnt/c/Users/<u>/JarvisOS/print-handoff/<spec_id>-<sha8>.3mf)
                                            |
     cmd.exe /c start "" "C:\...\file.3mf"   (Windows file association -> Bambu Studio)
                                            |
     Bambu Studio: printer/filament presets, orientation, supports, slice, send (its own auth)
```

Responsibilities: **JarvisOS** owns geometry truth, units, manifold/validation evidence, mesh tolerance and provenance (manifest hash ties the 3MF to its spec). **Bambu Studio** owns everything printer-specific. The boundary is a file, recorded with its SHA-256 in the manifest.

Notes: use a Windows-local path (not `\\wsl$`) so Bambu Studio's project save and recent-files behave normally. Keep the action local-only, enabled by config, and off by default under test/CI. Never build the shell command from user-controlled strings: pass args as a list and use only a derived, sanitized filename.

## 7. Bounded follow-up spec outline

**Title:** BLUECAD print handoff v0: mm-explicit 3MF export plus local open-in-slicer.

**Outcome:** For a validated BLUECAD candidate, the maintainer can download STL/STEP/3MF, or click "Open in slicer" and have the model open in Bambu Studio on Windows with the correct scale (mm) and one object per part.

**Scope:**
1. Add `model.3mf` to `ARTIFACT_NAMES` via `bd.Mesher(unit=Unit.MM)`, one object per `part_id` (name or `part_number` = part_id). Fixed tessellation tolerances recorded in the manifest. Hashes go into the manifest, with a determinism test under the pinned kernel (or a documented exemption if lib3mf output is not byte-stable).
2. Register `bluecad_step`, `bluecad_stl` and `bluecad_3mf` artifacts in `loop.py`, with correct MIME types in `routes.py` (`model/step`, `model/stl`, `model/3mf`).
3. Backend endpoint `POST /bluecad/artifacts/{id}/open-local` (feature-flagged, localhost only): copy to the configured Windows handoff directory, then run `cmd.exe /c start "" <winpath>` via `subprocess.run([...], shell=False, timeout=...)`. Return the path. No printer or network I/O.
4. Frontend download and open buttons on the candidate view.

**Non-goals:** slicing, G-code, Bambu settings metadata in 3MF, `bambu-connect://`, MQTT/FTP, access codes, cloud login, Farm Manager, embedding, OrcaSlicer plugin work, multi-material or color assignment.

**Evidence / acceptance:** unit tests that the 3MF unit is `millimeter` and there is one object per part. Bbox of the reloaded 3MF/STL matches `manifest.assembly.bbox_mm` within tolerance. Artifact-route tests for the new types. The open-local endpoint is mocked in tests (no real `cmd.exe`), and refuses when the flag is off. Manual proof: a screenshot or log of Bambu Studio opening a sample part at the correct size on the maintainer's machine, with the Bambu Studio version recorded.

**Possible later (separate spec, only if wanted):** optional sandboxed CLI slicing to a `.gcode.3mf` from pinned, flattened profiles, then handoff via `bambu-connect://import-file`. Still no credentials in JarvisOS.

## 8. What NOT to do

- Do not store or process printer access codes, serials, Bambu account tokens or cloud credentials.
- Do not implement MQTT/FTPS printer control, and do not require Developer Mode. JarvisOS would then start physical actions, and the interface is unsupported and revocable.
- Do not embed, vendor, fork or link Bambu Studio, OrcaSlicer or the network plugin (AGPL contamination, proprietary plugin, wx UI).
- Do not use `bambustudio://` / `bambustudioopen://` URLs (allowlisted, fail silently).
- Do not generate Bambu `project_settings.config` / plate metadata (undocumented and changes between versions).
- Do not depend on community re-signing or "open networking" plugins (legally contested, PR still open).
- Do not make slicer CLI output part of deterministic evidence (not byte-deterministic).

## Unverified / gaps

- Wiki pages (Bambu Connect, third-party integration, STEP) blocked (HTTP 402). Content comes from search snippets and the forum announcement.
- Whether Bambu Studio 2.8.x still keeps every CLI flag listed in the GitHub wiki was not tested locally.
- Bambu Studio's handling of 3MF objects without Bambu metadata on the maintainer's version (expected to import as plain objects, using the printer preset the user has selected) needs the manual proof above.
- The Developer Mode status on the newest firmware for the maintainer's specific printer model was not checked per model.
