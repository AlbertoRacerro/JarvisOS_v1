# 171 — Environment profiles

State: **ready**. This spec combines definition, contract and readiness under the maintainer directive of 2026-10-02 (continue the planned PBR roadmap in dependency order, with the [PBR engineering architecture record](../implementation/pbr-engineering-architecture-2026-10-02.md) and the ranked engineering inventory as joint authority). Its dependency is 155. It gives a workspace a site and immutable, provenance-carrying time-series environment profiles (sun, air, sea), created offline from imported files or generators, together with the product's first time-series chart. 172 consumes these profiles. 171 runs no simulation.

The record's §11 defaults apply: **uPlot (MIT)** is the single chart library, and there is **no live weather or ocean API fetch**.

## Fresh evidence (master `f2eefa85`)

Code survey and measurements: `out/wpbr/a171.report.md`.

1. **No site, no time series.** No site or latitude/longitude model exists. Workspaces have only name, slug, description and status. The frontend has no chart library, and Vite has no chunk configuration.
2. **Storage precedents.** The `artifacts` table is workspace-scoped with `sha256` and `stored_path`. BLUECAD stores files under `artifacts/<workspace>/…` with SHA-256 manifests. Study runs use canonical `sha256:` digests. Nothing enforces immutable, content-addressed blobs. Data paths must come from `core/paths.py`.
3. **No upload path.** No `UploadFile` endpoint exists, and `python-multipart` is not installed. Artifact metadata accepts caller-supplied paths, so it is not a safe ingestion pipeline. The default AI policy is `STRICT_IP`.
4. **pvlib probe.** pvlib 0.16.1 (BSD-3) resolves with the backend pins (numpy 2.3, scipy 1.18, scikit-sundae 1.1.3) on Python 3.12.3. It adds pandas, h5py, requests, pytz and tzdata (≈32 MB pvlib including `LinkeTurbidities.h5`, ≈72 MB pandas, ≈12 MB h5py). Offline, it ran:
   - `Location.get_clearsky(model="ineichen")` with the packaged Linke data;
   - `spa_python`;
   - `read_epw` and `read_pvgis_tmy` on local files.
5. **uPlot.** uPlot 1.6.32 is ≈22 kB gzip plus 1.9 kB CSS, imperative, so it needs a small React lifecycle wrapper.
6. **107 inputs.** PAR is `peak_par·sin(π(h − sunrise)/photoperiod)` in daylight and 0 at night. Temperature is mean + amplitude·sin over the day (`pbr_evaluator.py`).

## Decision

**A profile is an immutable, content-addressed artifact. Its digest is its identity, and an edit makes a new profile linked to its parent.** Site is a small revisioned workspace document. All computation is local: files are parsed from validated staged local paths, and generators use pvlib's packaged data.

- New backend dependencies: `pvlib==0.16.1` and the `pandas` version it resolves, pinned in `backend/requirements.txt`. The BSD-3 licence and package sizes are recorded in the dependency notes. New frontend dependency: `uplot` (MIT), in a lazily loaded chunk so unrelated routes don't pay for it.
- Upload uses a **raw request body** (`application/octet-stream`, filename as a query parameter). This avoids adding a multipart dependency.

Alternatives rejected:

- **Live PVGIS/ERA5/CMEMS fetch:** parked (record F12) until a provider setting with egress approval and credentials exists.
- **Mutable profiles:** a scenario must reference exactly the data it ran on, as `(profile_id, digest)`.
- **Chart.js or Recharts:** larger, or not time-series native. Either would still need the table fallback.

## Accepted capability

1. **Site (revisioned workspace document, CAS).**
   - Fields: name; latitude [−90, 90]°; longitude [−180, 180]°; elevation (m); IANA timezone (validated against tzdata); water-body label.
   - Generators use the current site. Every generated profile embeds the site snapshot it used.
2. **Profile artifact.**
   - **Time base.** Timestamps are stored in UTC at a fixed resolution (allowed: 5, 10, 15, 30 or 60 min, and 1 day). The display timezone comes from the site. Gaps are explicit `null`, never silently interpolated.
   - **Channels.** Each channel is optional and has a fixed SI storage unit and allowed display units: GHI, DNI and DHI (W m⁻²); PAR (µmol m⁻² s⁻¹); air temperature and sea temperature (K, displayed °C); wind speed (m s⁻¹); cloud cover (fraction 0–1); wave height (m); wave period (s). Values outside physical bounds are refused at creation, naming the channel and timestamp (negative irradiance, temperature outside 200–350 K, cloud outside [0, 1]).
   - **Content.** Canonical JSON with a fixed key order and float formatting. The digest is `sha256:<hex>` of those bytes.
   - **Storage.** Stored under a `core/paths.py`-owned workspace location. The file name is the digest, and the file is never overwritten. It is registered in `artifacts` with `sha256` and kind `environment_profile`. A read re-verifies the digest and refuses on mismatch.
   - **Metadata.** Name, channels with units, resolution, start/end, `parent_digest` (for edits), and provenance:
     - import: original filename, original file SHA-256, detected format, column mapping, unit choices and parser (pvlib function and version, or the Jarvis CSV parser version);
     - generator: kind, parameters, site snapshot, pvlib version.
3. **Import (bounded, local only).**
   - Upload: a raw body of at most 20 MB, with filename extension `.csv` or `.epw`. The file is staged under the workspace data root with a server-generated name. Path components in the client filename are ignored.
   - Detection: EPW goes through `pvlib.iotools.read_epw`. PVGIS-TMY CSV goes through `read_pvgis_tmy`. Any other CSV goes through a Jarvis parser with a **preview and mapping step**: the operator sees the detected columns and the first rows, maps a timestamp column (with its timezone or UTC offset) and value columns to channels, and picks units. Only then is the profile created.
   - Parsers receive only the validated staged path, never a URL. Parse failures are reported with line or column. Staged files are deleted after creation or after 24 h.
4. **Generators.**
   - `clear_sky`: pvlib `Location(site).get_clearsky(times, model="ineichen")` with the packaged Linke turbidity, multiplied by a clearness factor in [0, 1]. Solar position uses `spa_python`. It outputs GHI, DNI and DHI.
   - `synthetic_day`: the 107 forms. PAR is half-sine with peak, sunrise and photoperiod; temperature is mean + amplitude·sin. It is bit-identical to `pbr_evaluator`'s prescribed inputs at the same parameters (107 continuity).
   - `derived_par`: an explicit operation that creates a PAR channel from GHI with a visible, editable conversion factor (default 2.06 µmol J⁻¹ ≈ 0.45 PAR fraction × 4.57 µmol J⁻¹). It is labelled "screening conversion". Nothing is converted implicitly.
5. **Edit.** Table edits (cell values, or scaling or offsetting a channel over a range) create a **new** profile with `parent_digest` and an edit summary in its provenance. The original is unchanged.
6. **Operator UI.**
   - An **Environment** panel reachable from the Process stage toolbar ("Environment…"). It contains the site form, the profile list (name, channels, span, resolution, source kind, short digest), and the profile editor.
   - **Profile editor.**
     - A uPlot chart: one series per selected channel, a unit-aware axis per unit family, and zoom/pan synchronized with the table.
     - A paginated, keyboard-navigable **table fallback** that is always available and holds the editable values.
     - A provenance panel.
     - Import wizard and generator forms.
   - Accessible legend toggles. Readable at 1280 and 1440 CSS px without horizontal overflow. No raw JSON in the normal view.
7. **API.** Workspace-scoped endpoints:
   - site get and put (CAS);
   - profile list and read (metadata, values with range and resolution, digest);
   - upload, preview and confirm;
   - generate;
   - derive;
   - edit (returns the new profile).

   The surface stays headless-usable for 172. No agent actions in 171.

## Boundaries / non-goals

- No live API fetch, no outbound network in import or generate paths (tests enforce this), no scenario, no simulation, no tube or array optics (174), no change to the 107 evaluator contract.
- No SQL migration beyond registering artifacts in the existing `artifacts` table. Site and profiles live under the data root.
- FMU-neutral boundary (record §4.4): profiles are typed, unit-bearing time series exportable as CSV.

## Required evidence

- Focused backend tests:
  - site validation and CAS;
  - canonical bytes and digest stability; immutability (no overwrite) and read-time digest verification, including a tampered file;
  - channel bounds and gaps;
  - EPW and PVGIS-TMY import on checked-in small fixtures, and a CSV mapping round-trip with units and timezone;
  - the upload size and extension limits and path-component stripping;
  - parse error location;
  - `clear_sky` against a reference: the NREL SPA test case (Reda & Andreas 2004: 2003-10-17 12:30:30 −7 h, 39.742476°N, 105.1786°W, 1830.14 m) gives zenith 50.11162° and azimuth 194.34024° within 1e-4°; GHI is 0 at night and the clearness factor scales it;
  - `synthetic_day` bit-identity with 107;
  - `derived_par` labelling;
  - edits create linked profiles;
  - **no network**: socket creation is blocked during import and generate tests.
- `pvlib` and `pandas` pinned; CI install green; licence notes.
- Frontend build with uPlot in a separate lazy chunk. Node contract tests for the panel, wizard, the table fallback and lazy import.
- Exact-head **real Chromium** acceptance at 1280 and 1440 CSS px:
  - set the site;
  - generate a 3-day clear-sky profile at 15 min and see the plot with day/night shape;
  - import a checked-in EPW fixture and a CSV through the mapping step and plot both;
  - derive PAR;
  - edit a value in the table: a new profile appears with its parent link, and the original is unchanged;
  - the provenance panel is visible;
  - keyboard-only table navigation works;
  - the backend log shows no outbound network.
- Screenshots inspected; no raw JSON visible.
