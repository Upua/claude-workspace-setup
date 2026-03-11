---
name: cad-3d-printing
description: OpenSCAD design, STL generation, FDM-printable parts, enclosures, and validation with BOSL2 patterns
---

# CAD / 3D Printing Skill

## When This Skill Applies
Any task involving OpenSCAD design, STL generation, FDM-printable parts, enclosures,
brackets, mounts, or hardware integration. Load automatically on triggers in `config.yaml`.

---

## Core Workflow: Design-Verify Loop

**Measure → Model vitamin → Design → Render & inspect → Validate mesh → Review**

Iterate until the print-ready checklist (section 5) passes completely.

### Render Commands
```bash
# STL export
openscad -o output.stl input.scad

# Preview image (front-ish angle)
DISPLAY=:0 openscad --render --imgsize=1280,960 -o preview.png input.scad

# Custom camera angles for enclosures:
#   Front:  --camera=0,0,0,0,0,0,120
#   Back:   --camera=0,0,0,0,0,180,120
#   Top:    --camera=0,0,0,90,0,0,120
#   Iso:    --camera=0,0,0,55,0,25,120

# Mesh validation
admesh output.stl

# CGAL warning check (should print 0 warnings)
openscad -o /dev/null input.scad 2>&1 | grep -i warn
```

---

## OpenSCAD Conventions (always follow)

1. **BOSL2 first.** `include <BOSL2/std.scad>` at top. Prefer `cuboid()`, `cyl()`,
   `diff()`, `tag()`, `attach()`, `position()` over raw `cube()`/`cylinder()`.
2. **Named parameters.** Every dimension is a named variable at the top of the file.
   Zero magic numbers in geometry code.
3. **Explicit tolerances.** `tolerance = 0.4;` as a named variable, applied visibly
   where pockets/slots are cut.
4. **Resolution.** `$fn = 64;` globally for print renders, `$fn = 32;` for fast preview.
5. **No coplanar faces.** Overlap boolean operands by 0.1mm to prevent CGAL
   non-manifold warnings. E.g., `translate([0,0,-0.05]) cube([w, d, h+0.1])`.
6. **File structure:**
   ```
   // Part: <name>
   // Material: PETG | PLA | ABS
   // Print orientation: <which face down>
   // Supports: none | <strategy>
   // ──────────────────────────────
   // Parameters
   // Render call
   // Modules
   ```

---

## FDM Quick Reference

| Property              | PLA    | PETG   | ABS    |
|-----------------------|--------|--------|--------|
| Pocket clearance/side | 0.3mm  | 0.4mm  | 0.4mm  |
| Min wall thickness    | 1.2mm  | 1.6mm  | 1.6mm  |
| Min feature size      | 0.8mm  | 1.0mm  | 1.0mm  |
| Max bridge span       | 10mm   | 8mm    | 6mm    |
| Max overhang angle    | 60deg  | 55deg  | 50deg  |
| Snap-fit max strain   | 3%     | 5%     | 4%     |
| Shrinkage             | ~0.2%  | ~0.4%  | ~0.7%  |
| Min screw boss wall   | 2.0mm  | 2.4mm  | 2.4mm  |

Full tables: `knowledge/fdm-tolerances.md`

---

## Print-Ready Checklist

Before declaring any part print-ready, verify ALL items:

- [ ] **Manifold mesh:** `admesh file.stl` reports 0 errors
- [ ] **CGAL clean:** `openscad -o /dev/null file.scad 2>&1` shows 0 warnings
- [ ] **Wall thickness** >= material minimum everywhere
- [ ] **No unsupported overhangs** beyond material max angle
- [ ] **Pocket/slot dims** include tolerance allowance
- [ ] **Snap-fits/clips** have correct deflection geometry for material
- [ ] **Cable/FPC exits** have clearance and strain relief
- [ ] **Print orientation** specified in file header comment
- [ ] **Support strategy** documented (or confirmed none needed)
- [ ] **Preview rendered** from 3+ angles and visually inspected
- [ ] **Dimensions verified** against real hardware measurements

---

## Specialist Agents

| Agent          | Spawn When              | Deliverable                              |
|----------------|-------------------------|------------------------------------------|
| cad-researcher | Starting new project    | Prior art links, reference dimensions    |
| cad-validator  | After design iteration  | admesh + CGAL results, tolerance audit   |
| cad-reviewer   | Before finalizing       | Full checklist pass, design critique     |

**Default is solo** (no agents) for single-file or simple tasks.
Spawn agents only for multi-part assemblies or complex enclosures.

Agent definitions: `agents/`

---

## Knowledge Files (load as needed)

| File                            | Contents                                    |
|---------------------------------|---------------------------------------------|
| `knowledge/fdm-tolerances.md`   | Full material property tables               |
| `knowledge/openscad-patterns.md`| BOSL2 idioms, diff/tag patterns, modularity |
| `knowledge/enclosure-design.md` | Snap-fits, hinges, vents, IP rating, seals  |
| `knowledge/hardware-vitamins.md`| Real hardware dims (cameras, PCBs, screws)  |
| `knowledge/references.md`       | Curated open-source project index           |

---

## Common Pitfalls

- **Coplanar union faces** cause CGAL failures silently in preview but break STL export.
  Always offset cut volumes by 0.05-0.1mm.
- **Inner dimensions print smaller** than modeled on FDM. Always add pocket tolerance.
- **Thin walls** (< 1.2mm) may not slice as solid perimeters. Check in slicer preview.
- **Forgetting strain relief** on cable exits leads to FPC damage. Add a channel or clip.
- **Boolean with flush faces** at Z=0 causes first-layer artifacts. Raise parts 0.01mm
  or extend cuts below Z=0.
- **Never use `intersection()` to split bodies** — intersecting a full-height shape with
  a cutting plane creates coplanar edges at the split, causing green artifacts. Instead,
  build each half as its own primitive at the target height (e.g., two `rounded_box()`
  calls at `half_d` height instead of one at `outer_d` intersected with a cutting cube).
- **Center holes at wall midpoint, not at the wall face** — `cylinder(h=X, center=true)`
  placed at a face only penetrates half its height into the wall. Position at
  `translate([0, 0, face + wall/2]) cylinder(h = wall + 1, center = true)`.
- **Backface green is normal in F6** — In CGAL render mode, interior surfaces (normals
  pointing away from camera) display green. Only green on *exterior* faces indicates
  non-manifold geometry. Rotate the view to confirm before debugging.
- **Assembly previews need exploded views** — Parts touching at Z=0 create overlapping
  geometry that fails CGAL (`Simple: no`). Use a gap of at least `pin_h + 1mm` between
  mating parts in assembly mode.
- **Anti-coplanar epsilon pattern** — Define `e = 0.1;` at top of file. Every boolean
  cut overshoots by `e` on faces that would otherwise be flush with the parent solid.
  Pins/bosses overlap `e` into their parent for clean unions. This single pattern
  prevents all coplanar artifacts.
