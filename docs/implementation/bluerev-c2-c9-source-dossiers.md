# BlueRev C2–C9 source dossiers

Date: 2026-10-24. Also published as [issue #922](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/922).

Prepared by a maintainer-assigned cloud session from the **18 October 2026 manual** (*Fotobioreattori — scelte tecniche e casi di riferimento*, 31 pp., replication cards pp. 25–26 and the referenced sections), which is the same edition spec 212 used for C1. Each case lists:
- the primary source;
- what to conserve;
- the reference observations, exactly as the manual states them;
- what is missing or not reported (**NR**);
- cautions the manual already raises;
- the JarvisOS capability owners likely needed;
- a bounded first comparison.

**Status of this material.** This is entry evidence, like `docs/implementation/212-c1-source-and-capability-audit.md`, not a replication claim. Numbers are copied from the manual's summaries of the primary sources. **Before a case is run, the coordinator must re-read the primary paper**, because the manual's summary is not the primary authority, as 212 established. The primary hosts were not reachable from the cloud sandbox, so access was not checked here.

Use the spec 212/215 verdict vocabulary (reproduced / partially reproduced / not determinable / discrepant). Use declared-assumption bands (#905) where forcing or parameters are missing; never contact authors (maintainer decision on #905). Run cases inside the new Design shell (#901 Phase 1). CFD is needed only where noted (#901 Phase 2, spec 216).

**Scheduling (maintainer):** this is reference material, not new work by itself. Use it when each C case starts, in the order already set (#901 comment of 2026-10-23, #918). Do not start C2 before the current 216 / #918 / #907 / #920 commitments.

**Manual's recommended order:**
- C1–C4 as the tubular reference;
- C5–C6 to compare the flexible solution and materials;
- C7–C9 when that subsystem becomes decisive.

---

### C2 · Two-layer tubular manifold with airlift (Molina et al. 2001, [S21])

- **Source:** Molina Grima et al., *Tubular photobioreactor design for algal cultures*, J. Biotechnol. 2001, pp. 113–131. Locators: §3.2, §4.1–4.4, Figs. 5–7, Table 1. DOI 10.1016/S0168-1656(01)00353-4.
- **Conserve:**
  - 200 L total; tubes ID/OD 53/60 mm (rigid PMMA); 80 m of tube on two levels (about 12 m² footprint).
  - Free spacing 90 mm horizontal and 30 mm vertical.
  - Airlift 4 m tall, riser/downcomer ID 53 mm, gas separator 220 mm long with a 60° bottom.
  - *P. tricornutum* UTEX 640; manifold in a water bath at 20 ± 2 °C.
- **Design rationale to reproduce (C, then E):**
  - 18 spacing combinations were tested. Beyond about 100 mm horizontal spacing the irradiance gain becomes small.
  - Compacting onto two levels costs −17 % surface irradiance against a widely spaced single layer, but gives more volume per area.
  - The 80 m tube length comes from u = 0.5 m/s, O₂ production 0.003 mol/m³/s, inlet assumed at 100 % and design outlet at 300 % air saturation (§4.1). Higher peaks were observed, so 300 % is a design criterion, not a biological limit.
  - Below 4 m of airlift height, u = 0.5 m/s was not reached. Design kLa is 0.13 s⁻¹ (= 7.8 min⁻¹); velocity, holdup and transfer were then measured.
- **Reference observations (Table 1):**
  - At 0.50 and 0.35 m/s: 1.19 and 1.15 g/L/day, with no significant difference.
  - At 0.17 m/s the culture was lost. That is an observed collapse limit, not a target to reproduce.
  - The runs had different daily irradiances.
- **Airlift operating range:** superficial air 0.005–0.031 m/s, liquid 0.17–0.50 m/s. Circulation and gas exchange are coupled.
- **Missing / NR:** sparger and separator details (only in the original figures); time-aligned irradiance for each velocity run.
- **Capabilities:**
  - geometry with two-level spacing and shading (174 T2; Design components);
  - airlift hydraulics as a gas–liquid circulation curve (not a pump with head);
  - axial O₂ build-up along 80 m (170/172 lack an axial O₂ model, the gap noted in 212);
  - PBR growth (170) with a *P. tricornutum* card.
  - CFD not required.
- **First bounded comparison:** reproduce the design arithmetic first, which needs no biology:
  - tube length from the O₂ balance;
  - airlift height needed for 0.5 m/s, from a holdup/drag model;
  - the irradiance penalty of the two-level layout.

  Then compare productivity at 0.50/0.35 m/s as a declared-assumption band.

### C3 · Centrifugal pump and cell damage, 40 L rigid loop (Michels et al. 2016, [S04])

- **Source:** Michels et al., *Cultivation of shear stress sensitive and tolerant microalgal species in a tubular photobioreactor equipped with a centrifugal pump*, J. Appl. Phycol. 28, 53–61 (2016). DOI 10.1007/s10811-015-0559-8. Locators: Methods, Results, Tables 3–4, Fig. 4, shear-stress calculation.
- **Conserve:**
  - 40 L; 20 m of tube, ID/OD 43.6/50 mm.
  - Pump ARBO SealPro **KR-32-95**: impeller 95 mm, 32 mm discharge, inverter. 2.0–3.6 m³/h, starting at 600 rpm (about 0.37 m/s).
  - Temperature 20 ± 0.5 °C; *T. suecica* turbidostat at about 0.52 ± 0.05 g/L.
- **Reference observations:**
  - *T. suecica* grows.
  - *I. galbana*, *S. costatum* and *C. muelleri* did not grow even at 2 m³/h.
  - At 3.6 m³/h fouling appeared within a day and increased over two weeks, with no immediate productivity drop for *T. suecica*.
- **Pump data:**
  - The brochure gives H–Q and power curves only at 2950/1450 rpm, and the test ran down to 600 rpm.
  - NPSHr is not in the brochure (NR).
  - Head, rpm and power at the operating point: **NR**.
- **Caution:** the case does **not** determine *N. gaditana* tolerance.
- **Capabilities:**
  - pump/hydraulics owners (047/072, 107): affinity-law rescaling of the 2950/1450 rpm curves to 600 rpm, declared as an assumption;
  - shear estimate (the paper's analytic shear calculation);
  - a viability/damage model, which JarvisOS does not have. This would be a Studio custom model (correlation with stated validity), not core physics.
- **First bounded comparison:** reproduce the paper's shear-stress levels per flow rate and the pump operating point from the affinity laws. Report the biological outcome as a classification (grows / does not grow) against the computed shear, not as a fitted damage law.

### C4 · Floating 110 L film tubes with side-stream gas treatment (OMEGA, Wiley et al. 2013, [S03])

- **Source:** Wiley et al., *Microalgae Cultivation Using Offshore Membrane Enclosures for Growing Algae (OMEGA)*, J. Sustainable Bioenergy Systems 3, 18–32 (2013). DOI 10.4236/jsbs.2013.31003 (open, publisher HTML). Locators: §2.2–2.5, §3.1–3.3, Figs. 1–3, 7. Related: [S30] CEC-500-2013-143 for the 1600 L scale-up.
- **Conserve:**
  - **Circuit and pumps:**
    - 110 L; two LLDPE film tubes (0.381 mm), ID 114 mm × 3 m, in an 8 800 L seawater tank with a night cover.
    - Main loop 86–130 L/min (0.14–0.21 m/s), pump ITT Goulds 1MC1D5D0 on a 1 HP GS-2 inverter. 1 HP is the inverter rating, not measured power.
    - Side stream about 5 L/min via a SHURflo 2088-343-135 diaphragm pump (12 VDC, voltage-regulated).
  - **Gas train:**
    - **O₂ cascade:** five PVC plates of 20 cm², vessel Ø152 mm × 0.30 m.
    - **CO₂ contactor:** Ø76 mm × 2.13 m, diffuser 22 cm² at 1.8 m from the top, gas 8.5 % CO₂ in air.
    - **Settling chamber:** Ø152 mm × 0.91 m, protruding side inlet 0.30 m, 13 mm drain.
  - **Mixing:** six swirl elements (PE augers) with 51 mm PVC collars, 0.9 m apart.
  - **Control:** CO₂ on demand at pH 7.60 in the side column.
- **Reference observations:**
  - **Height scan** (3 m test column; levels 0.3/0.6/0.9/1.8/2.1/2.7 m; gas 0.5 L/min): more height and higher pH increased transfer.
  - **Adopted point:** about 1.8 m of head, pH 7.0–8.25, efficiency about 50 %, kLa(CO₂) 0.21 ± 0.01 min⁻¹ (SE, n = 3).
  - **Measured transfer** 1.69 × 10⁻⁴ mol/L/min against an estimated demand of 8.72 × 10⁻⁶ mol/L/min at 20 g/m²/day: ratio about 19.4, with a sizing safety factor of 1.5.
  - **Turnover:** side-stream 5/110 L/min, about 22 min nominal; main loop about 0.85–1.28 min. These are nominal figures, not measured residence-time distributions.
  - **Settling:** never above 14 %.
  - **Swirl elements:** more fouling at the inserts and more resistance. There is no smooth-tube control, so productivity gains cannot be attributed to them.
- **Cautions:**
  - The DO probe saturated at **212 %**, so the plateau does not prove O₂ control below that.
  - The 23-day freshwater consortium productivity is **not** transferable to a marine culture.
  - Swirl elements are not an optimised solution.
- **Missing / NR:** O₂ removal capacity of the cascade; pump head and rpm; measured electrical power.
- **Capabilities:**
  - side-stream topology in Process (Plant with a service branch);
  - CO₂ mass transfer and inorganic-carbon chemistry with pH (048 gas KPIs; 175 PBR-THERMAL-GAS-2 is planned, not ready, and is likely the real blocker);
  - settling (177 DOWNSTREAM-HARVEST-1 is planned).
  - CFD not required for the first pass.
- **First bounded comparison:** hydraulics first (loop flow vs. velocity, turnover times), then the **carbon balance** (supply vs. demand ratio) using the published kLa. The manual explicitly recommends this order: hydraulics, then kLa, then the C balance.

### C5 · Shallow closed film channel with two airlifts (Dogaris et al. 2015, [S02])

- **Source:** Dogaris et al., *A novel horizontal photobioreactor for high-density cultivation of microalgae*, Bioresour. Technol. 198, 316–324 (2015). DOI 10.1016/j.biortech.2015.09.030; author manuscript available (CC BY-NC-ND). Locators: §2.1, §3.1, §3.4–3.5, Tables 2–3, Fig. 1.
- **Conserve:**
  - **Channel:** PE film 0.15 mm, 133.5 × 68 cm, 5 cm nominal depth; 65 L **total including the airlifts**.
  - **Airlifts:** two acrylic airlifts at 10 L/min of gas each; CO₂ 2–3 %, pH 7.50 ± 0.10.
  - **Support and heat:** foam on the airlifts and bubble wrap on part of the bottom. Outdoor test in a temperature-controlled pool, so the thermal contact is part of the case.
- **Reference observations:**
  - *N. atomus* over 165 days: mean **18.2 g/m²/day**, maximum 4.3 g/L.
  - Film transmission 92.8 ± 0.7 % before vs. 92.0 ± 0.9 % (SE) after hypochlorite and neutralisation, with no inhibition observed.
- **Missing:** liquid flow rate, air-blower energy and the effective depth. The manual says to measure these, which means the paper does not give them as needed.
- **Cautions:**
  - The 65 L includes the airlifts, so illuminated volume and area must be separated.
  - Productivities must not be ranked against other cases without correcting species, climate, light, area and thermal control.
- **Capabilities:**
  - flat thin-layer geometry with optics (174 T2 is tube-oriented, so a flat-channel optical path may need a model);
  - airlift-driven circulation;
  - a thermal coupling to a water bath (175 planned).
  - CFD not required.
- **First bounded comparison:** areal productivity as a declared-assumption band, using site irradiance for the published location and period and a literature *N. atomus* card, against 18.2 g/m²/day. Keep the bath temperature as given.

### C6 · Wall materials and cleanability (Borucińska & Parfieniuk 2026, [S14]; context [S13], [S15])

- **Source:** Borucińska-Parfieniuk et al., *Degradation of Some Polymeric Materials of Bioreactors for Growing Algae*, Materials 19, 384 (2026). DOI 10.3390/ma19020384 (open, PMC12842760). Locators: §2, §3.3–3.4, §4.
- **Conserve:**
  - Materials PMMA, recycled PMMA, PC, PC2UV and PET, with the same finish, exposure and cleaning cycle.
  - Specimens 25 × 290 × 3 mm, one per material, with readings in several zones.
  - LED lighting, salinity 20 ‰, *Thalassiosira pseudonana*, 70 days.
- **Reference observations:**
  - **Residual loss at 450–700 nm after cleaning:** PC 11.3 %, recycled PMMA 2.4 %.
  - **Variable-level (waterline) zone:** PC/PMMA transmission 36.36/49.39 % after exposure and 81.38/90.98 % after cleaning. The waterline can be more critical than the always-wet wall.
  - **[S13] context:** PMMA used for 1 460 days lost 5–25 % transmission depending on zone and wavelength, with scratches and residues in crevices. Washing with 1.5 % sulphamic acid for 12 h does not restore it.
- **Cautions:**
  - Zones on one specimen are **not independent replicates**.
  - This is not a multi-year marine test.
  - Manufacturer nominal transmission and measured spectral transmission are not interchangeable.
  - Cost comparisons in [S35] Table 6.4 are historical and use different geometries.
- **Capabilities:**
  - material optical properties in the optics model (wall transmission, from the #920 decision on OD/ID/wall);
  - a time-varying fouling or transmission-loss factor (a Studio custom model);
  - a spectral treatment, which T2 likely does not have (PAR-integrated).
- **First bounded comparison:** this is not a growth replication. Encode the published transmission before and after cleaning as material cards, and show the effect of the measured losses on PAR delivered to a C1 tube (sensitivity), with the replicate limitation stated.

### C7 · Tangential ultrafiltration harvesting (Mora-Sánchez et al. 2024, [S12])

- **Source:** Mora-Sánchez et al., *Ultrafiltration Harvesting of Microalgae Culture Cultivated in a WRRF: Long-Term Performance and Techno-Economic and Carbon Footprint Assessment*, Sustainability 16, 369 (2024). DOI 10.3390/su16010369 (open). Locators: §2.1–2.3, Fig. 1, Tables 2–4, energy and cleaning sections.
- **Conserve:**
  - **Module:** ROMICON HF 5.0-43-PM500, L 1 m, 1 m², 500 kDa, flow cross-section 0.0003 m².
  - **Tanks and pumps:** feed 0.7 m³, retentate 0.04 m³, CIP 0.2 m³; separate pumps for feed, tangential flow and backwash.
  - **Pressures and velocity:** TMP 1.25 ± 0.02 bar; inlet 2.11 ± 0.04 bar, outlet 0.48 ± 0.02 bar; crossflow 1.2 ± 0.3 m/s.
  - **Cleaning:** CIP with NaOCl 200 ppm, 10 min, about every 150 h, plus cycle backwashes.
- **Reference observations:**
  - 78 cycles over 212 days; 450 ± 65 L/cycle.
  - Concentration from 0.50 ± 0.12 to 9.7 ± 1.7 g/L; concentration factor 21 ± 6.
  - J20 = 16 ± 8 L/m²/h.
  - Energy 1.51 ± 0.64 kWh/kg harvested and 0.76 ± 0.32 kWh/m³ fed.
- **Cautions:**
  - The culture is a Coelastrella/Desmodesmus consortium in wastewater, **not** marine *Nannochloropsis*, so compatibility with strain and medium comes first.
  - A modest TMP does not mean low energy: the tangential recirculation dominates.
  - Retaining cells does not restore the medium, so recycle needs a growth check.
- **Capabilities:**
  - a harvest unit in Process (177 DOWNSTREAM-HARVEST-1 is planned, not ready);
  - pump energy for crossflow (047/072);
  - membrane flux/fouling as a Studio custom unit (correlation with validity) rather than core physics.
- **First bounded comparison:** reproduce the **energy per m³ and per kg** from the published pressures, crossflow velocity, cross-section, cycle volumes and concentration factor, as a mass-and-energy balance with no fouling model. Compare against 0.76 ± 0.32 kWh/m³ and 1.51 ± 0.64 kWh/kg.

### C8 · Floating models in waves and mooring (Zhu et al. 2019, [S09]; numerical [S10])

- **Source:** Zhu et al., *Hydrodynamic performance of floating photobioreactors driven by wave energy*, Biotechnol. Biofuels 12, 54 (2019). DOI 10.1186/s13068-019-1396-9 (open, CC BY). Locators: Methods, Tables 1–2, Figs. 1–3, Discussion. Numerical companion: Zhu et al. 2023, Front. Mar. Sci. 10, 1095590.
- **Conserve:**
  - **Models:** 1:10 scale, about 1 m² of useful area. Square 1 × 1 m (outer 1.12 × 1.12 m) vs. rectangle 1.7 × 0.6 m (outer 1.82 × 0.72 m).
  - **Fill:** 5, 10 or 20 L, i.e. 0.5–2 cm of liquid.
  - **Waves:** H 2–10 cm, T 0.8–1.8 s.
  - **Mooring:** two schemes, with and without floats.
- **Reference observations:**
  - The square model moves more; shape affects motion and load.
  - Mooring-load extremes of 10.5 N without floats and 0.67 N with floats are not a universal pair. The load sensor was rated 10 N, so check the peak.
  - Algal productivity was **not measured**.
- **Numerical [S10]:** square, rectangle and cylinder; liquid 0.05–0.25 m; 0.01 m translation and 10° roll. The response depends on shape, frequency and free surface, and is **not directly transferable to a full tube**.
- **Cautions:**
  - Froude similarity is needed to change scale.
  - Wave energy alone does not prove that recirculation, stripping and level control are sufficient.
- **Capabilities:**
  - #901 **Motion/Mechanics** stage, still a placeholder: rigid-body heave/roll response to regular waves, which is a new capability;
  - sloshing would need CFD with a free surface (beyond spec 216's single-phase slice);
  - mooring load as a simple quasi-static/dynamic line model.
- **First bounded comparison:** no biology. Reproduce motion amplitude trends (square vs. rectangle) and mooring-load order of magnitude over the published H/T grid with a linear-wave rigid-body model. Report it as a Motion/Mechanics capability qualification, not a productivity claim. This case is the natural trigger for specifying Motion/Mechanics.

### C9 · Gas-permeable back wall for O₂ removal with little aeration (Kishi thesis summary, [S31]; related [S32], [S37])

- **Source:** Kishi, thesis summary *Oxygen removal efficiency from microalgal culture by gas-permeating photobioreactor*, 4 pp., PDF dated 2018 (Soka University repository). This is distinct from [S32], Kishi et al. 2021, Algal Res. 102543, of which only the abstract was recovered.
- **Conserve:**
  - **Panel:** 600 × 450 × 20 mm; transparent PP front.
  - **Back wall:** hydrophobic microporous film 0.02 mm, 0.2 µm pores. Transmission through it is under 20 % with about 80 % reflection: optics and exchange are separated, and the lit face is not shaded.
  - **Control:** an equal PP panel with the same mixing.
  - **Culture:** *A. platensis* at pH 9.8; air 1 min every 20; stirring 12 s every 2 min.
- **Reference observations:**
  - kLa(O₂) **0.061 min⁻¹**: below the 0.13 design target, but more than ten times the PP control.
  - Productivity 1.98 g/L/day at PPFD 325 µmol/m²/s.
  - [S32] abstract (Euhalothece, permeable vs. non-permeable bag): steady-state O₂ less than half, kLa 0.084 min⁻¹ with continuous mixing. Full configuration not recovered.
  - [S37] abstract (hollow fibres for CO₂): kLa(CO₂) 0.0148/0.0133 vs. 0.0070 min⁻¹ for bubbling.
- **Cautions:**
  - Alkaline pH 9.8 biology does not transfer to *Nannochloropsis*.
  - If the medium or external phase changes (a fully immersed tube, a second liquid phase), test the transfer first.
  - This is not yet the best reference for a fully immersed tube.
- **Capabilities:**
  - wall-based O₂ mass transfer as a boundary term in the PBR gas balance (175 planned);
  - optical treatment of a reflective back wall (T2 extension).
  - CFD not required.
- **First bounded comparison:** reproduce the kLa ratio (permeable vs. control) and the steady-state O₂ difference from a lumped gas balance with the published kLa and O₂ production. Treat growth as secondary.

---

### Cross-cutting notes for the coordinator

- **Blocking capabilities across cases:**
  - **175 PBR-THERMAL-GAS-2** (planned) blocks C2 (axial O₂), C4 (carbon/pH), C5 (bath), C9 (wall O₂).
  - **177 DOWNSTREAM-HARVEST-1** (planned) blocks C4 settling and C7.
  - **Motion/Mechanics** (#901 placeholder) blocks C8.

  Expect each to become a spec when its case starts, sized to that case only.
- **CFD (spec 216)** is not required for the first pass of any C2–C9 case. It becomes useful for C3 (local shear), C4 (swirl elements) and C8/S10 (sloshing) only after the lumped comparison.
- **Units traps flagged by the manual:**
  - kLa 0.13 s⁻¹ = 7.8 min⁻¹;
  - kLa for O₂ and for CO₂ are not comparable across media or apparatus;
  - in I = I₀·exp(−k_a·X·z), X must be in g/m³ (1 g/L = 1000 g/m³).
- **Strain mismatches:**
  - C2 *P. tricornutum*; C3 *T. suecica* and others; C4 freshwater consortium; C5 *N. atomus*; C6 *T. pseudonana*; C7 consortium; C9 *A. platensis*.
  - None is BlueRev's *N. gaditana*. Keep each case's organism. The biological control the manual recommends is a short-path, temperature-controlled reference ([S06] *N. gaditana*: μmax 0.0256 h⁻¹, I_K 15.28 µmol/m²/s, kd 0.0046 h⁻¹; effective attenuation is geometry-dependent, not universal).
- **C1 follow-up discrepancy (from the same manual, for #905):** the stripper cylinders (Ø0.24 and Ø0.37 m, 2.2 m tall) are about 100 and 237 L, against the 150 and 310 L reported in the 2015 campaign. Do not invent a height to reconcile them.

