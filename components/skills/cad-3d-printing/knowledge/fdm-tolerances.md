# FDM 3D Printing Tolerances — Comprehensive Reference

Detailed tolerance data for FDM printing with a 0.4mm nozzle at 0.2mm layer height.
Loaded on-demand when precise fit/clearance values are needed.

---

## 1. Dimensional Tolerances by Material

All values are **per side** unless noted otherwise.

### Pocket / Slot Clearance

Extra space added per side so a component drops into a pocket or slot.

| Material | Clearance per Side | Notes |
|----------|-------------------|-------|
| PLA | 0.2 - 0.3 mm | Low shrinkage, tight fit possible |
| PETG | 0.3 - 0.5 mm | Slight ooze widens inner walls; use 0.4 mm default |
| ABS | 0.3 - 0.5 mm | Shrinkage pulls walls inward; compensate generously |

### Hole Sizing

Holes consistently print smaller than designed due to inner-wall compensation and material contraction.

| Hole Diameter (designed) | Add to Radius | Result |
|--------------------------|---------------|--------|
| < 5 mm | +0.3 - 0.4 mm | Small holes close up the most |
| 5 - 15 mm | +0.2 - 0.3 mm | Standard range |
| > 15 mm | +0.2 mm | Large holes are more accurate |

PLA tends toward the low end; PETG and ABS toward the high end of each range.

### Press-Fit Interference

Negative clearance (part is oversized relative to hole) for friction-held inserts.

| Material | Interference per Side | Notes |
|----------|----------------------|-------|
| PLA | -0.1 to -0.2 mm | Brittle; risk of cracking if too tight |
| PETG | -0.15 to -0.25 mm | Slight flex helps absorb press-in forces |
| ABS | -0.15 to -0.25 mm | Similar to PETG; acetone-weld option available |

### Slip-Fit Clearance

Easy insertion by hand, component slides freely but does not rattle.

| Fit Type | Clearance per Side |
|----------|-------------------|
| Slip fit | 0.1 - 0.2 mm |
| Loose / removable | 0.2 - 0.3 mm |

### Shaft-in-Hole Fit

For a shaft rotating or sliding inside a printed hole:

- Design shaft radius **0.15 - 0.3 mm smaller** than hole radius.
- Print the hole slightly oversized (see Hole Sizing above).
- Combined effect gives a functional running clearance of ~0.3 - 0.5 mm diametral.

---

## 2. Shrinkage Compensation

| Material | Linear Shrinkage | Compensation Strategy |
|----------|-----------------|----------------------|
| PLA | 0.3 - 0.5 % | Minimal; usually safe to ignore |
| PETG | 0.3 - 0.8 % | Mostly in Z; compensate on tall parts (>50 mm) |
| ABS | 0.7 - 1.0 % | Significant; must compensate for precision parts |

**Key rule:** Inner dimensions shrink more than outer dimensions. A pocket will be smaller than designed; an outer shell will be closer to nominal. Always validate inner dims first.

For ABS precision parts, scale the model by 1/(1 - shrinkage). Example at 0.8%: scale factor = 1.008.

---

## 3. Minimum Feature Sizes

All values assume 0.4 mm nozzle, 0.2 mm layer height.

| Feature | Minimum | Notes |
|---------|---------|-------|
| Wall thickness (PLA) | 1.2 mm (3 perimeters) | Thinner walls are fragile and may delaminate |
| Wall thickness (PETG/ABS) | 1.6 mm (4 perimeters) | PETG/ABS need extra perimeter for rigidity |
| Pin / post diameter | 2.0 mm | Below this, posts snap easily |
| Hole diameter | 1.5 mm | Holes < 1.5 mm tend to close up entirely |
| Slot width | 1.0 mm | Narrower slots fuse shut during printing |
| Embossed/debossed text height | 0.6 mm | At least 3 layers tall at 0.2 mm LH |
| Text stroke width | 0.5 mm | Needs to be > 1 nozzle width |
| Gap between parallel walls | 0.5 mm | Below this, walls may fuse together |

**Perimeter math:** wall thickness = N * nozzle_diameter. At 0.4 mm nozzle: 3 perimeters = 1.2 mm, 4 = 1.6 mm, 6 = 2.4 mm.

---

## 4. Overhang and Bridge Limits

### Maximum Unsupported Overhang Angle (from vertical)

| Material | Max Angle | Notes |
|----------|-----------|-------|
| PLA | 60 deg | Excellent overhang performance |
| PETG | 55 deg | Slight stringing on overhangs |
| ABS | 50 deg | Warping and curl reduce overhang quality |

Angles beyond these limits require support material or design changes.

### Maximum Bridge Span (horizontal, no support underneath)

| Material | Max Span | Notes |
|----------|----------|-------|
| PLA | 10 mm | Good bridging with cooling |
| PETG | 8 mm | Sags more; slow speed helps |
| ABS | 6 mm | Poor bridging; avoid where possible |

### Practical Design Rules

- **Chamfers over fillets** on bottom edges. Chamfers start at 45 deg and print cleanly without support. Fillets on bottom surfaces sag.
- **Elephant foot:** The first layer squishes ~0.2 mm wider than designed. For precision base features, apply a 0.2 mm chamfer or compensate in the slicer.
- **Teardrop holes:** Horizontal holes benefit from a teardrop top (45 deg point) to eliminate the need for support inside the hole.

---

## 5. Snap-Fit Design Parameters

### Cantilever Deflection Formula

```
deflection = (permissible_strain * length^2) / (0.67 * thickness)
```

Where length and thickness are in mm, strain is a decimal (e.g., 0.03 for 3%).

### Maximum Permissible Strain

| Material | Max Strain | Notes |
|----------|-----------|-------|
| PLA | 3 % | Brittle; snaps break if over-deflected |
| PETG | 5 % | Good flexibility for snap-fits |
| ABS | 4 % | Decent snap performance |
| Nylon | 8 % | Best for repeated snap engagement |

### Recommended Dimensions

| Parameter | Small Enclosures | Structural |
|-----------|-----------------|------------|
| Cantilever thickness | 1.0 - 1.5 mm | 1.5 - 2.0 mm |
| Cantilever length | 5 - 10 mm | 10 - 15 mm |
| Undercut depth | 0.3 - 0.8 mm | 0.8 - 1.5 mm |

Longer cantilevers deflect more easily and reduce insertion force.

### Geometry

- **Lead-in angle:** 30 - 45 deg (ramp for easy assembly).
- **Retaining angle:** 80 - 90 deg (near-vertical to resist disassembly).
- **Print orientation:** Cantilever must run along layer lines (XY plane), never bridging across them. Clips printed perpendicular to layers snap off under deflection.

---

## 6. Layer Adhesion and Strength

### Anisotropic Strength (Z vs XY)

| Material | Z Tensile Strength (% of XY) | Notes |
|----------|------------------------------|-------|
| PLA | 50 - 70 % | Layers separate cleanly; brittle fracture |
| PETG | 60 - 80 % | Better interlayer bonding than PLA |
| ABS | 55 - 75 % | Acetone vapor smoothing improves bonding |

### Orientation Guidelines

- **Structural parts:** Orient so primary load acts in the XY plane, not pulling layers apart (Z).
- **Enclosures:** Print with the opening facing up. Side walls then have continuous, unbroken layer lines for maximum strength.
- **Snap-fit clips:** Orient so clip deflection occurs in the XY plane. Clips deflecting in Z will delaminate.
- **Screw bosses:** Print vertically so the screw threads cut across layers (stronger pull-out resistance).
- **Thin walls under bending:** Orient so the bending force compresses layers rather than peeling them apart.

---

## 7. Project Defaults

These are the baseline values used in our OpenSCAD designs unless overridden.

| Parameter | Default Value | Rationale |
|-----------|--------------|-----------|
| Printer type | Standard FDM | Prusa-class or similar |
| Nozzle diameter | 0.4 mm | Most common; good detail/speed balance |
| Material | PETG | Strength, flexibility, temperature resistance |
| Layer height | 0.2 mm | Standard quality; good strength |
| Infill | 30 % gyroid | Good omnidirectional strength |
| Pocket tolerance | 0.4 mm per side | Middle of PETG range |
| Wall thickness | 2.4 mm (6 perimeters) | Rigid, structural walls |
| `$fn` (circle segments) | 64 | Smooth curves without excessive render time |

### Quick OpenSCAD Snippet

```openscad
// Project tolerance constants
tol       = 0.4;   // pocket clearance per side (PETG)
wall      = 2.4;   // default wall thickness
$fn       = 64;    // circle resolution

module pocket(size) {
    // size = [x, y, z] of the component
    cube([size.x + 2*tol, size.y + 2*tol, size.z + tol]);
}
```
