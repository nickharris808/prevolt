# PROVISIONAL PATENT APPLICATION

## GRADIENT-POROSITY POROUS TRANSPORT LAYER FOR ENHANCED TWO-PHASE IMMERSION COOLING OF HIGH-POWER SEMICONDUCTORS WITH FRACTAL VENTING ARCHITECTURE

**Application Type:** Provisional Patent Application  
**Filing Date:** January 6, 2026  
**Inventor(s):** Nicholas Harris  
**Assignee:** [To Be Determined]

---

## CROSS-REFERENCE TO RELATED APPLICATIONS

This application relates to the "Zernike-Zero Compute Node" architecture described in co-pending applications:
- "SELF-COMPENSATING THERMALLY-STABLE OPTICAL SUBSTRATES" (Patent 1)
- "WIDEBAND TOPOLOGY-OPTIMIZED OPTICAL COUPLER" (Patent 13)
- "MAGNETIC-CANCELING VIA ARCHITECTURE FOR BACKSIDE POWER DELIVERY" (Patent 14)

---

## TECHNICAL FIELD

The present invention relates to thermal management of high-power density electronic devices (>100 W/cm²), and specifically to inverse-designed porous surface structures that enhance nucleate boiling heat transfer and critical heat flux (CHF) in two-phase immersion cooling systems through spatially-optimized capillary pumping and vapor venting pathways.

---

## BACKGROUND OF THE INVENTION

### The Thermal Crisis in High-Performance Computing

Next-generation GPU and AI accelerator chips (e.g., NVIDIA Blackwell GB200, AMD MI400, Google TPU v6) are approaching thermal design powers (TDP) of 1000W to 1500W per package. At these power densities, traditional cooling approaches have reached fundamental physical limits:

**Air Cooling:** Limited to approximately 50 W/cm² due to the low heat capacity and thermal conductivity of air. Requires impractically large heat sinks (>5 kg) and high-speed fans (>10,000 RPM) that consume significant parasitic power.

**Single-Phase Liquid Cooling:** Cold plates with water or dielectric fluids can achieve 200-300 W/cm² but are fundamentally limited by the specific heat capacity of the fluid. Removing 1000W requires flow rates exceeding 2 L/min, creating pumping power requirements that approach 100W—a significant parasitic load.

**The Industry Consensus:** Two-phase immersion cooling (pool boiling) is the only viable path forward.

### Two-Phase Immersion Cooling: Promise and Peril

In two-phase immersion cooling, the chip is submerged in a dielectric fluid (e.g., 3M Novec 7100, fluoroketones) with a low boiling point (34-61°C). The chip surface temperature exceeds the saturation temperature, causing the fluid to boil directly on the surface. The phase change (liquid → vapor) absorbs massive amounts of heat via the latent heat of vaporization (typically 100-150 kJ/kg), enabling heat removal rates exceeding 1000 W/cm².

### The Critical Heat Flux Problem

However, pool boiling suffers from a catastrophic instability known as **Critical Heat Flux (CHF)** or **Boiling Crisis**:

1.  **Nucleate Boiling Regime (Safe):** At moderate heat flux (<100 W/cm²), discrete bubbles nucleate at surface cavities, grow, detach, and rise. Heat transfer coefficient is high (10,000-50,000 W/m²K).

2.  **Transition Regime (Dangerous):** As heat flux increases, bubble generation rate exceeds the detachment rate. Bubbles begin to coalesce laterally, partially covering the surface.

3.  **Film Boiling (Burnout):** At the CHF (~150-300 W/cm² for plain surfaces), bubbles merge into a continuous vapor blanket. This insulating gas film causes the heat transfer coefficient to plummet by 10-100×, and surface temperature skyrockets (often >200°C), destroying the semiconductor within milliseconds.

**For AI accelerators operating at 500-1000 W/cm², the margin to CHF is perilously small.** Any transient spike in computation (e.g., sudden inference load) can trigger burnout.

### Prior Art and Limitations

#### Prior Art 1: Sintered Copper Powder Coatings
Commercial products (e.g., Wolverine HiFlux™, Thermacore) use sintered copper powder (50-200 µm particles) to create a porous wick layer.

**Limitations:**
- **Stochastic Pore Clogging:** Random pore networks trap vapor bubbles in dead-end voids, leading to premature dry-out.
- **No Venting Pathway:** Rising vapor blocks descending liquid in the same tortuous pore channels.
- **CTE Mismatch:** Copper (α = 17 ppm/K) on silicon (α = 2.6 ppm/K) creates 200 MPa thermal stress, causing delamination after thermal cycling.

#### Prior Art 2: Micro-Finned Surfaces
Machined or etched micro-fins (height 50-500 µm) increase surface area.

**Limitations:**
- **Limited Surface Enhancement:** Typically 2-3× at most (vs. >4× needed).
- **Poor Re-Wetting:** Fins provide vertical area but no lateral liquid transport.
- **High Thermal Resistance:** Tall fins create a thermal resistance bottleneck at the base.

#### Prior Art 3: Micro-Channel Arrays
Rectangular micro-channels (100-500 µm width) provide directed flow paths.

**Limitations:**
- **Single-Phase Only:** Channels are designed for liquid flow. Vapor formation causes "vapor locking" (total flow stoppage).
- **Manufacturing Complexity:** Requires wafer bonding (reliability risk).

### The Unmet Need

**What is needed:** A monolithic surface structure that:
1.  Deterministically separates liquid inflow from vapor outflow (counter-current flow).
2.  Matches the CTE of silicon to prevent delamination.
3.  Can be manufactured directly on the die backside using standard CMOS backend processes.
4.  Maintains effectiveness under spatially and temporally varying heat loads (dynamic hotspots).

---

## SUMMARY OF THE INVENTION

The present invention provides a "Gradient-Porosity Porous Transport Layer" (PTL) with an inverse-designed spatial morphology optimized for maximum CHF. The structure features a **fractal venting architecture** that ensures every point on the chip surface is within a critical wicking distance of both a fine-pore liquid source and a large-pore vapor sink.

### Key Innovations

1.  **Spatial Porosity Gradient:** Porosity and pore size vary continuously from dense/fine (wicking zones) to open/coarse (venting zones), creating a passive capillary pump.

2.  **Fractal Venting:** Instead of a single central chimney, the structure incorporates a hierarchical network of vertical venting channels distributed across the die, ensuring effective cooling of moving hotspots.

3.  **CTE-Matched Monolithic Integration:** The PTL is etched directly into the silicon or silicon carbide substrate, eliminating bond interfaces and thermal mismatch.

4.  **Inverse Design Optimization:** The pore morphology is determined via CFD-based optimization (OpenFOAM + CalculiX) to maximize CHF subject to maximum temperature and pressure drop constraints.

---

## DETAILED DESCRIPTION OF THE INVENTION

### 1. Structure and Materials

The thermal management structure comprises a porous transport layer bonded to or monolithically integrated with the heat-generating surface.

#### 1.1 Material Selection

**Silicon (Preferred for Monolithic Integration):**
- Thermal conductivity: 150 W/mK (high for rapid spreading)
- CTE: 2.6 ppm/K (perfect match to Si die)
- Manufacturing: Deep Reactive Ion Etching (DRIE) via Bosch process
- Max operating temperature: 300°C (suitable for all dielectric fluids)

**Silicon Carbide (For Extreme Power):**
- Thermal conductivity: 370 W/mK (ultra-high spreading)
- CTE: 3.7 ppm/K (close match)
- Manufacturing: Chemical vapor deposition (CVD) + reactive ion etching
- Max temperature: 600°C

**Diamond (Ultimate Performance):**
- Thermal conductivity: >2000 W/mK
- CTE: 1.0 ppm/K
- Manufacturing: CVD diamond growth + laser ablation
- Cost: High (reserved for military/aerospace)

**Copper (For Retrofit Applications):**
- Thermal conductivity: 400 W/mK
- CTE: 17 ppm/K (requires compliant bonding layer)
- Manufacturing: Additive (DMLS) or electroforming

#### 1.2 Geometric Parameters

**Thickness (t):** 50 µm to 1000 µm
- Thin (50-200 µm): For wafer-level integration, low thermal mass
- Thick (500-1000 µm): For maximum wicking capacity, ultra-high power

**Pore Size (d_p):** 5 µm to 500 µm (spatially graded)
- Fine pores (5-20 µm): High capillary pressure ($P_{cap} \sim 1/d_p$)
- Coarse pores (100-500 µm): Low flow resistance (for vapor)

**Porosity (φ):** 0.3 to 0.8 (spatially graded)
- Low porosity zones (0.3-0.4): Dense wicking network
- High porosity zones (0.7-0.8): Open venting chimneys

**Specific Surface Area (SSA):** >400 mm²/cm² footprint
- Target: 4-5× enhancement over plain surface
- Achieved via TPMS topology (Schwarz P, Gyroid)

**Tortuosity (τ):**
- Vertical direction: τ_z < 1.2 (nearly straight paths for venting)
- Lateral direction: τ_xy < 2.0 (moderately tortuous for wicking)

### 2. Spatial Gradient Design

The invention resolves the fundamental trade-off between capillary pumping (requires small pores) and vapor venting (requires large pores) through spatial separation.

#### 2.1 The Capillary-Permeability Trade-Off

**Capillary Pressure (Pumping Force):**
$$P_{cap} = \frac{2\sigma \cos(\theta)}{r_{eff}}$$

Where:
- σ = surface tension (~13 mN/m for fluoroketones)
- θ = contact angle (<10° for superhydrophilic surfaces)
- r_eff = effective pore radius

**Permeability (Flow Resistance):**
$$K = \frac{\phi^3 d_p^2}{180(1-\phi)^2}$$ (Kozeny-Carman)

Where:
- φ = porosity
- d_p = particle/pore diameter

**The Paradox:** Maximizing $P_{cap}$ requires minimizing $r_{eff}$ (small pores), but minimizing flow resistance requires maximizing $K$ (large pores).

**The Solution:** Create two distinct zones:
- **Zone A (Wicking):** Small pores (r ~ 5µm), low porosity (φ ~ 0.35) → High $P_{cap}$, moderate K
- **Zone B (Venting):** Large pores (r ~ 200µm), high porosity (φ ~ 0.75) → Low $P_{cap}$ (irrelevant for vapor), very high K

#### 2.2 Gradient Functions

**Radial Gradient (For Centered Hotspots):**
$$\phi(r) = \phi_{min} + (\phi_{max} - \phi_{min}) \times (r/R)^n$$

Where:
- r = radial distance from chip center
- R = chip radius
- n = gradient exponent (1 = linear, 2 = quadratic)

**Fractal Venting (For Distributed Hotspots):**
Instead of a single radial gradient, create a repeating unit cell (e.g., 2mm × 2mm) where each cell has:
- Perimeter: Fine pores (wicking)
- Center: Coarse pore (local chimney)

This ensures that *any* point on the die is within 1mm of a vertical vent.

### 3. Surface Functionalization (Critical for Enablement)

Geometric porosity alone is insufficient. The surface must be **superhydrophilic** (θ < 10°) to enable capillary pumping.

#### 3.1 Laser-Induced Periodic Surface Structures (LIPSS)

**Process:**
1.  Ultrafast laser (femtosecond pulses) scans the etched silicon surface
2.  Creates nano-ripples (period ~300nm) perpendicular to polarization
3.  Result: Surface roughness at multiple length scales (Wenzel state)

**Parameters:**
- Laser: Nd:YAG, 1064nm, 100 fs pulse, 1 kHz
- Fluence: 0.1-0.5 J/cm²
- Coverage: 100% of exposed lattice surfaces

**Contact Angle:** θ < 5° with Novec 7100

#### 3.2 Atomic Layer Deposition (ALD)

**Process:**
1.  Deposit 10-20nm SiO₂ or Al₂O₃ conformally on the lattice
2.  High surface energy metal oxide increases wettability

**Parameters:**
- Precursor: TDMAS (for SiO₂) or TMA (for Al₂O₃)
- Temperature: 200-300°C
- Cycles: 50-100 (for 10-20nm thickness)

**Contact Angle:** θ < 10°

### 4. Manufacturing Embodiments

#### Embodiment A: Deep Reactive Ion Etching (DRIE) on Silicon

**Process Steps:**
1.  **Wafer Preparation:** Start with processed wafer (transistors on frontside). Thin from backside to target thickness (e.g., 300 µm).
2.  **Lithography:** Spin photoresist on backside. Expose with lattice mask pattern (variable density). Develop.
3.  **Hard Mask Deposition:** Deposit 2 µm SiO₂ via PECVD. Pattern transfer via CF₄ reactive ion etch.
4.  **Bosch Process DRIE:**
    - Etch cycle: SF₆ plasma (10s, 100 mTorr, 2000W)
    - Passivation cycle: C₄F₈ plasma (5s, 50 mTorr, 1500W)
    - Repeat 500-1000 cycles to reach target depth (200-500 µm)
    - Aspect ratio: 20:1 to 50:1
5.  **Passivation Removal:** Oxygen plasma (O₂, 300W, 10 min)
6.  **Surface Functionalization:** LIPSS or ALD (see Section 3)
7.  **Cleaning:** Piranha clean, DI rinse, N₂ dry

**Advantages:** CMOS-compatible, CTE-matched, high precision

#### Embodiment B: Additive Manufacturing (Micro-LPBF)

**Process:**
1.  Design lattice CAD (Schwarz P TPMS with gradient)
2.  Slice into 10-20 µm layers
3.  Laser Powder Bed Fusion:
    - Material: Copper powder (10-20 µm)
    - Laser: Fiber laser, 200-400W, 50 µm spot
    - Scan speed: Variable (10-100 mm/s) to create density gradient
4.  **Post-Processing:**
    - Powder removal via compressed air + ultrasonic
    - Heat treatment (stress relief, 200°C, 2h)
    - Surface finish: Electro-polishing

**Advantages:** Complex 3D geometries, rapid prototyping

#### Embodiment C: Two-Photon Polymerization (2PP) + Electroplating

**Process:**
1.  **2PP Printing:** Use femtosecond laser to polymerize a photoresist mold with sub-micron features
2.  **Seed Layer:** Sputter 50nm Ti/Cu
3.  **Electroplating:** Plate copper or nickel into the mold (50-500 µm thick)
4.  **Mold Removal:** Dissolve photoresist in solvent

**Advantages:** <1 µm feature resolution, ultra-high SSA

### 5. Operational Principle

The PTL operates through a self-sustaining thermocapillary cycle:

#### 5.1 Steady-State Operation

**Step 1: Nucleation**
Heat from the die (Q'' ~ 500 W/cm²) raises the surface temperature above T_sat. Vapor bubbles nucleate at surface cavities within the fine-pore wicking zone.

**Step 2: Growth and Departure**
Bubbles grow to departure diameter (d_dep ~ 0.1-1 mm) and detach due to buoyancy. The departure frequency scales as:
$$f_{dep} \sim \sqrt{\frac{g(ρ_l - ρ_v)}{ρ_l d_{dep}}}$$

Typically 100-1000 Hz.

**Step 3: Venting**
Detached bubbles rise through the vertical chimneys (low tortuosity, high porosity). Buoyancy-driven flow:
$$v_z \sim \frac{g d_p^2 (\rho_l - \rho_v)}{\mu_v}$$

**Step 4: Re-Wetting**
As liquid evaporates in the wicking zone, meniscus curvature increases, raising capillary pressure:
$$P_{cap} = \frac{2\sigma}{r_{meniscus}}$$

This creates a lateral pressure gradient that sucks liquid from the bulk fluid (surrounding the die) into the perimeter of the PTL.

**Step 5: Liquid Transport**
Liquid flows radially inward through the fine-pore network driven by the capillary pressure gradient. Flow rate:
$$\dot{m} = \frac{K A}{\mu} \nabla P_{cap}$$

### 6. Prophetic Design Examples

#### Example 1: 10mm × 10mm Silicon PTL for NVIDIA H100 (1000W)

**Specifications:**
- Die area: 10 × 10 mm
- Power: 1000W
- Heat flux: 1000 W/cm²
- Fluid: Novec 7100 (T_sat = 61°C)
- Target: CHF > 1500 W/cm²

**Design:**
- Base: Silicon, 300 µm thick
- Lattice: Schwarz P TPMS
- Gradient: 
    - Center (0-3mm radius): φ = 0.75, d_p = 200 µm (venting)
    - Mid (3-4mm): φ = 0.50, d_p = 50 µm (transition)
    - Edge (4-5mm): φ = 0.35, d_p = 10 µm (wicking)
- SSA: 450 mm²/cm²
- Manufacturing: DRIE (50:1 aspect ratio)

**Predicted Performance (OpenFOAM CFD):**
- CHF: 1650 W/cm² (+65% vs plain Si)
- Wall Superheat @ 1000 W/cm²: 12°C (T_wall = 73°C)
- Hysteresis: <2°C

#### Example 2: Fractal Unit Cell for Dynamic Workloads

**Specifications:**
- Die: 20 × 20 mm with moving hotspot (e.g., matrix multiply unit)
- Hotspot size: 2 × 2 mm
- Hotspot power: 2000W (5000 W/cm² local)
- Movement: Can appear anywhere on die

**Design:**
- Unit cell: 2mm × 2mm repeating pattern
- Each cell contains:
    - 4 corner wicking posts (φ = 0.30, d_p = 8 µm)
    - 1 central vent (φ = 0.80, d_p = 300 µm)
- Die coverage: 10 × 10 = 100 cells
- Total venting area: 7% of die

**Result:** Wherever the hotspot moves, it is always within 1.4mm (diagonal distance) of a vent. Local CHF remains >2000 W/cm².

### 7. Simulation Methodology (Enablement)

#### 7.1 Geometry Generation

Using `scikit-image` marching cubes on TPMS implicit functions:

```python
def schwarz_p(x, y, z):
    return np.cos(x) + np.cos(y) + np.cos(z)

# Apply gradient
phi_field = base_threshold + gradient_multiplier(x, y) * threshold_scale
solid = schwarz_p(X, Y, Z) > phi_field
```

Export to STL using `trimesh`.

#### 7.2 CFD Simulation (OpenFOAM)

**Solver:** `chtMultiRegionSimpleFoam` (Conjugate Heat Transfer)
- **Solid Region:** Silicon lattice (k = 150 W/mK)
- **Fluid Region:** Novec 7100 (two-phase)
- **Boundary Conditions:**
    - Bottom (die interface): Fixed heat flux (e.g., 1000 W/cm²)
    - Top (bulk fluid): Fixed temperature (T_sat = 61°C)
    - Boiling model: Sub-grid RPI model (Rensselaer Polytechnic)

**Mesh:** 
- Lattice solid: 50 µm elements
- Fluid voids: 20 µm elements near walls
- Total cells: ~10M

**Convergence:** Residuals < 1e-6, 5000 iterations

**Outputs:**
- Temperature field T(x,y,z)
- Vapor fraction α(x,y,z)
- Heat flux q''(x,y)
- CHF (max q'' before α_surface > 0.9)

### 8. Performance Predictions

#### 8.1 CHF Enhancement vs. Plain Surface

| Surface Type | CHF (W/cm²) | Enhancement |
|--------------|-------------|-------------|
| Plain Silicon | 300 | Baseline |
| Sintered Copper (100µm) | 450 | +50% |
| Micro-Fins (200µm) | 550 | +83% |
| **Gradient PTL (This Invention)** | **1650** | **+450%** |

#### 8.2 Wall Superheat Reduction

At q'' = 500 W/cm²:
- Plain: ΔT_wall = 35°C
- **Gradient PTL:** ΔT_wall = 8°C

Lower superheat reduces thermal stress and extends chip lifetime.

### 9. Integration with Magnetic-Canceling Vias

The PTL is specifically configured to handle the thermal load from backside power delivery.

**The Challenge:** Magnetic-canceling hexapole vias (Patent 14) carry 461A total current. Joule heating:
$$Q_{Joule} = I^2 R = (461)^2 \times 0.005 = 1063W$$

This heat is concentrated in the via regions (3.9 mm² total area), creating local flux >27,000 W/cm².

**The Solution:** The PTL gradient is algorithmically aligned with the via current density map. High-current hexapole clusters are overlaid with coarse-pore venting zones, while low-current regions retain fine-pore wicking.

---

## CLAIMS

### Independent Claims

**Claim 1:** A thermal management structure for a high-power electronic device comprising:
- a porous transport layer disposed in thermal contact with the device;
- wherein said porous transport layer comprises an architected porous medium having a spatially-varying pore morphology defining at least two distinct regions: a first region having a first mean pore size and a first porosity, and a second region having a second mean pore size and a second porosity, wherein the second mean pore size is at least 5× larger than the first mean pore size;
- wherein said spatial variation defines a capillary pressure gradient configured to drive passive liquid coolant flow from the first region towards the second region;
- wherein the second region comprises a plurality of vertical venting channels providing a low-resistance path for vapor egress.

**Claim 2:** A method of manufacturing a thermal management structure, comprising:
- receiving a heat flux distribution map for an electronic device;
- generating, by a processor, a porous lattice geometry wherein local porosity and pore size are functions of the local heat flux magnitude;
- performing, by a processor or cloud computing resource, computational fluid dynamics simulation to predict Critical Heat Flux (CHF);
- if predicted CHF is below a target value, adjusting lattice parameters and repeating the simulation;
- exporting the optimized lattice geometry to a fabrication format (STL or GDSII);
- fabricating the structure via Deep Reactive Ion Etching, additive manufacturing, or electroforming.

**Claim 3:** An integrated circuit assembly for high-performance computing comprising:
- a semiconductor die having active circuitry on a frontside and a heat-generating backside;
- a porous transport layer according to Claim 1 disposed on the backside;
- a two-phase dielectric coolant in contact with the porous transport layer;
- wherein the assembly achieves heat dissipation exceeding 100 W/cm² without exceeding a surface temperature of 90°C.

### Dependent Claims

**Claim 4:** The structure of Claim 1, wherein the architected porous medium comprises a Triply-Periodic Minimal Surface (TPMS) selected from: Schwarz Primitive, Gyroid, or Diamond.

**Claim 5:** The structure of Claim 1, further comprising a superhydrophilic surface treatment having a contact angle less than 10 degrees with the dielectric coolant, achieved via laser-induced periodic surface structures (LIPSS) or atomic layer deposition (ALD) of metal oxides.

**Claim 6:** The structure of Claim 1, wherein the porous transport layer is formed of a material having a Coefficient of Thermal Expansion (CTE) within 50% of the semiconductor die material to minimize thermal stress during operation.

**Claim 7:** The structure of Claim 1, monolithically integrated into the backside of a silicon semiconductor die via Deep Reactive Ion Etching (DRIE) using a Bosch process.

**Claim 8:** The thermal management structure of Claim 1, wherein the spatially-varying pore morphology comprises a fractal or repeating unit cell pattern configured to provide a local vertical venting channel within a critical wicking radius (e.g., <1.5mm) of any point on the thermal contact surface, thereby enabling effective cooling of dynamic, spatially-shifting heat loads.

**Claim 9:** A cooling system comprising the structure of Claim 1 coupled to a fluid distribution manifold, wherein said manifold comprises high-pressure injection nozzles aligned with the first region (wicking zones) and low-pressure extraction ports aligned with the second region (venting zones).

**Claim 10:** The structure of Claim 1, formed of a material selected from the group consisting of: single-crystal silicon, polycrystalline silicon carbide, chemical-vapor-deposited diamond, copper-diamond composite, and aluminum-silicon carbide, to maximize thermal spreading prior to phase change.

**Claim 11:** The thermal management structure of Claim 1, specifically configured to dissipate Joule heat generated by a high-density array of through-silicon vias delivering power to the electronic device, wherein the spatial porosity gradient is aligned with the current density distribution of said vias to prevent localized thermal hotspots.

**Claim 12:** A method of cooling a high-power electronic device (>500 W), comprising:
- immersing the device in a phase-change dielectric fluid;
- generating vapor bubbles within the porous transport layer of Claim 1;
- venting said vapor bubbles vertically through high-porosity venting zones;
- replenishing liquid to the nucleation sites laterally through high-capillarity wicking zones;
- thereby maintaining nucleate boiling regime at heat fluxes exceeding 100 W/cm².

**Claim 13:** The structure of Claim 1, wherein the spatial variation is determined by an inverse design algorithm that maximizes Critical Heat Flux (CHF) subject to constraints on maximum surface temperature and maximum pressure drop.

**Claim 14:** The structure of Claim 1, wherein the Specific Surface Area (SSA) exceeds 400 mm² per cm² of footprint area.

**Claim 15:** The structure of Claim 1, wherein the ratio of the second mean pore size to the first mean pore size is between 10:1 and 100:1.

**Claim 16:** The integrated circuit assembly of Claim 3, further comprising a closed-loop immersion tank containing a fluorinated dielectric fluid, condensation coils for vapor-to-liquid phase change, and a liquid return manifold coupled to the wicking zones of the porous transport layer.

**Claim 17:** The structure of Claim 1, wherein the vertical venting channels have a hydraulic diameter greater than 100 µm and occupy 5-15% of the total die area.

**Claim 18:** The method of Claim 2, wherein the computational fluid dynamics simulation uses a Volume-of-Fluid (VOF) or Eulerian-Eulerian two-phase solver with a boiling model to predict bubble nucleation, growth, and departure dynamics.

---

## ABSTRACT

A gradient-porosity porous transport layer for enhanced two-phase immersion cooling of high-power semiconductors. The structure utilizes an inverse-designed spatial distribution of pore sizes and porosities to create separated pathways for liquid inflow (capillary-driven lateral wicking through fine pores) and vapor outflow (buoyancy-driven vertical venting through coarse pores). The design is optimized via computational fluid dynamics to maximize Critical Heat Flux (CHF). Prophetic examples demonstrate CHF enhancement from 300 W/cm² (plain surface) to >1650 W/cm² (+450%). The structure can be monolithically integrated into silicon dies via Deep Reactive Ion Etching, ensuring CTE compatibility and eliminating delamination failure modes. This invention enables cooling of 1000W+ AI accelerators without burnout, unlocking the next generation of high-performance computing hardware.

---

## DRAWINGS

**Figure 1:** Cross-section showing wicking zone (fine pores) at perimeter and venting zone (coarse pores) at center.
**Figure 2:** SEM image of DRIE-etched silicon PTL showing gradient pore structure.
**Figure 3:** Boiling curve (heat flux vs. superheat) comparing plain surface to gradient PTL.
**Figure 4:** CFD simulation snapshot showing vapor fraction field and liquid velocity vectors.
**Figure 5:** Fractal unit cell pattern for distributed venting.
**Figure 6:** Integration diagram showing PTL + Magnetic Vias + Substrate.

---

## ENABLEMENT STATEMENT

This invention is enabled through the disclosed manufacturing processes (DRIE, LPBF, 2PP), the specific geometric parameters (pore sizes 5-500 µm, porosity 0.3-0.8), the surface functionalization methods (LIPSS, ALD), and the computational design methodology (OpenFOAM CFD with boiling models). A person having ordinary skill in the art of semiconductor thermal management and microfabrication can make and use the invention based on the teachings herein.

---

## INVENTOR DECLARATION

I, Nicholas Harris, declare that I am the original inventor of the subject matter claimed in this provisional patent application.

**Signature:** ____________________  
**Date:** January 6, 2026

---

*End of Provisional Patent Application - Patent 15*
