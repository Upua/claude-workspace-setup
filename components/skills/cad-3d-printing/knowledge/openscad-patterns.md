# OpenSCAD Coding Patterns & Conventions

Reference for writing clean, printable OpenSCAD with BOSL2.
Loaded on-demand when generating or editing `.scad` files.

---

## 1. File Structure Convention

Every SCAD file follows this layout:

```openscad
// Part Name — brief description
// Print: PETG, 0.2mm layer, 3 walls, 20% infill
// Orientation: prints upright / on its back / etc.
// ============================================================

include <BOSL2/std.scad>

$fn = 64;

// --- Parameters ------------------------------------------------
cam_w       = 25;     // camera PCB width
cam_h       = 24;     // camera PCB height
cam_d       = 11.5;   // camera module total depth (with AF)
wall        = 2;      // enclosure wall thickness
tolerance   = 0.4;    // per-side clearance for FDM pockets

// --- Derived ---------------------------------------------------
outer_w = cam_w + wall * 2 + tolerance * 2;
outer_h = cam_h + wall * 2 + tolerance * 2;
outer_d = cam_d + wall;

// --- Render ----------------------------------------------------
// Top-level call. Rotate if needed for print orientation.
housing();

// --- Modules ---------------------------------------------------
module housing() {
    // ...
}
```

**Rules:**
- Header always states part name, recommended print settings, and orientation.
- All literal dimensions live in the Parameters section as named variables.
- Derived values go in their own section so the dependency chain is visible.
- The Render section is a single top-level call (possibly wrapped in `rotate()`).
- Module definitions come last.

---

## 2. BOSL2 Essentials

### Primitives

Use BOSL2 primitives instead of raw OpenSCAD when you need rounding or anchoring.

```openscad
// Raw OpenSCAD
cube([30, 20, 10], center=true);
cylinder(d=10, h=5, center=true);

// BOSL2 — adds rounding, chamfering, and anchor support
cuboid([30, 20, 10], rounding=2);
cyl(d=10, h=5, rounding1=1);          // round bottom edge only
```

`sphere(d=d)` works fine as-is; BOSL2 does not add much there.

### Boolean Operations with Tagging

```openscad
diff()
  cuboid([30, 20, 10], rounding=2)     // body (auto "keep")
    tag("remove")
      position(TOP)
        cuboid([20, 10, 8]);           // pocket to subtract
```

This replaces the classic `difference() { outer(); inner(); }` pattern.
Advantage: tag multiple children as `"remove"` without deep nesting.

For unions, just place children inside the parent scope — BOSL2 unions implicitly.

### Attachment System

```openscad
cuboid([30, 20, 10])
  attach(TOP)           cuboid([10, 10, 5]);   // child sits on top
  position(RIGHT)       cyl(d=5, h=3);         // centered on right face
  attach(BOTTOM, TOP)   cuboid([8, 8, 3]);     // child's TOP on parent's BOTTOM
```

**Anchors:** `TOP`, `BOTTOM`, `LEFT`, `RIGHT`, `FRONT`, `BACK`, `CENTER`
**Edge anchors:** `TOP+RIGHT`, `BOTTOM+FRONT`, etc.

- `attach(parent_anchor)` — child grows outward from anchor face.
- `attach(parent_anchor, child_anchor)` — aligns specified child face to parent face.
- `position(anchor)` — moves child's center to the anchor point (no reorientation).

### When to Use BOSL2 vs Raw OpenSCAD

| Use BOSL2 for | Use raw OpenSCAD for |
|---|---|
| Primitives with rounding/chamfer | `hull()` |
| Boolean tagging (`diff()`) | `linear_extrude()`, `rotate_extrude()` |
| Attachment-based positioning | Complex `for` loops and paths |
| | `polygon()`, `polyhedron()` |

BOSL2 is not always simpler. If raw OpenSCAD is clearer for a specific construct, use it.

---

## 3. Parametric Variable Naming

- **snake_case**, descriptive: `cam_w`, `wall_thickness`, `lens_offset_y`
- **Group** related params with section comments:
  ```openscad
  // --- Camera Module ---
  cam_w = 25;
  cam_h = 24;

  // --- Enclosure ---
  wall = 2;
  tolerance = 0.4;
  ```
- **Derived values** in a separate section with visible formulas:
  ```openscad
  outer_w = cam_w + wall * 2 + tolerance * 2;
  ```
- **Tolerances** always named and applied visibly:
  ```openscad
  // GOOD — intent is clear
  pocket_w = pcb_w + tolerance * 2;

  // BAD — magic number hides tolerance
  pocket_w = 25.8;
  ```

---

## 4. Anti-Patterns

### Magic Numbers

```openscad
// BAD
translate([12.5, 12, 0]) cylinder(r=6.5, h=5);

// GOOD
lens_r = lens_dia / 2;
translate([cam_w/2 + lens_offset_x, cam_h/2 + lens_offset_y, 0])
    cylinder(r=lens_r + clearance, h=wall + 0.1);
```

### Coplanar Faces in Booleans

Coplanar faces produce non-manifold geometry and CGAL warnings.

```openscad
// BAD — subtracted face sits exactly at z=5
difference() {
    cube([10, 10, 10]);
    translate([0, 0, 5]) cube([5, 5, 5]);
}

// GOOD — overlap by 0.1mm in both directions
difference() {
    cube([10, 10, 10]);
    translate([0, 0, 4.9]) cube([5, 5, 5.2]);
}
```

### Excessive $fn

- `$fn = 64` is sufficient for FDM printing. `$fn = 128+` wastes render time for zero quality benefit.
- Use `$fn = 32` during iterative preview for speed.
- Never set `$fn` per-shape unless that shape specifically needs a different value.

### Deep Nesting

If you reach 4+ levels of `difference()/union()/intersection()`, refactor:

```openscad
// BAD — hard to read, hard to debug
difference() {
    union() {
        difference() {
            cube(...)
            cylinder(...)
        }
        cube(...)
    }
    cylinder(...)
}

// GOOD — named modules, each does one thing
module shell()  { ... }
module ports()  { ... }
module mount()  { ... }

difference() {
    union() { shell(); mount(); }
    ports();
}
```

---

## 5. Performance Tips

- **`render()`** around complex diffs inside modules triggers CGAL caching and speeds up preview.
- **Avoid `minkowski()`** unless absolutely needed — it is extremely slow. A `hull()` of offset shapes is often a viable alternative.
- **`hull()` of cylinders** is fast and produces good rounded boxes (see idiom below).
- **During iterative work:** lower `$fn` to 32, skip `render()`, use a smaller preview window.
- **Headless render:** `openscad -o output.stl input.scad` (no display needed).
- **Preview image:** `DISPLAY=:0 openscad --render --imgsize=1280,960 -o preview.png input.scad`
- **Custom camera angle:** `--camera=x,y,z,rotx,roty,rotz,dist`

---

## 6. Common Enclosure Idioms

### Rounded Box — hull method (raw OpenSCAD)

```openscad
module rounded_box(w, h, d, r=2) {
    hull() {
        for (x = [-1, 1], y = [-1, 1])
            translate([x * (w/2 - r), y * (h/2 - r), 0])
                cylinder(r=r, h=d, center=true);
    }
}
```

### Rounded Box — BOSL2 (preferred)

```openscad
cuboid([w, h, d], rounding=r, edges="Z");  // round only vertical edges
```

### Pocket with Tolerance

```openscad
diff()
  cuboid([pcb_w + wall*2, pcb_h + wall*2, pcb_depth + wall])
    tag("remove") position(TOP)
      cuboid([pcb_w + tol*2, pcb_h + tol*2, pcb_depth + 0.1]);
```

### Cable / Ribbon Exit Slot

```openscad
tag("remove") position(BACK)
  cuboid([ribbon_w + tol*2, wall + 0.2, ribbon_h]);
```

### Screw Boss

```openscad
module screw_boss(d_outer, d_hole, h) {
    diff()
      cyl(d=d_outer, h=h, anchor=BOTTOM)
        tag("remove")
          cyl(d=d_hole, h=h + 0.2, anchor=BOTTOM);
}
```

### Snap-Fit Lip

```openscad
// Lip on shell body
module lip(w, h, lip_h=1.5, lip_d=0.8) {
    position(TOP)
      cuboid([w, h, lip_h])
        position(TOP + FRONT)
          cuboid([w, lip_d, lip_d]);
}
```

---

## 7. FDM Print Tolerance Reference

| Feature | Tolerance per side | Notes |
|---|---|---|
| Pocket for PCB | 0.3 - 0.5 mm | 0.4 mm default for PETG |
| Press-fit hole | -0.1 to 0 mm | Test first |
| Sliding fit (pin in hole) | 0.2 - 0.3 mm | |
| Snap-fit clip | 0.3 mm | Flex clearance |
| Screw hole (self-tap) | drill dia - 0.3 mm | M3 -> 2.7 mm hole |
| Minimum wall (PETG) | 1.6 mm | < 1 mm is fragile |
| Minimum gap (separate parts) | 0.4 mm | Below this, fusion risk |

---

## 8. LLM-Specific Guidance

When generating OpenSCAD code:

1. **Always use named variables.** Resist the urge to inline calculations. Every number that means something gets a name.

2. **Prefer `position()` and `attach()` over `translate()`.** They are spatially intuitive and less error-prone than computing manual offsets.

3. **Mentally trace each placement.** After writing a `translate()` or `position()`, confirm the part ends up where intended. Off-by-half-width errors are the most common spatial bug.

4. **Render preview after every significant change.** Visual feedback catches spatial errors that code review misses. Use:
   ```bash
   DISPLAY=:0 openscad --render --imgsize=1280,960 -o preview.png file.scad
   ```

5. **Mark uncertain dimensions.** When unsure about a measurement, make it a parameter with a `// VERIFY` comment so it can be adjusted after a test print.

6. **Test booleans incrementally.** Render just the "remove" shapes first (comment out the `diff()`) to confirm they are positioned correctly before combining.

7. **Validate the STL before declaring done:**
   ```bash
   openscad -o output.stl input.scad 2>&1 | grep -i "warning\|error"
   admesh --no-fix output.stl | grep -E "edges|facets"
   ```
   Zero CGAL warnings + manifold mesh = ready to print.

8. **When splitting into multiple files** (e.g., housing + backplate), make each file fully self-contained. Shared parameters go into a `params.scad` that both files `include`.

---

## 9. Mesh Validation Checklist

Before declaring an STL ready to print:

```bash
# 1. Render and capture warnings
openscad -o part.stl part.scad 2>&1 | tee render.log
grep -ci "warning" render.log   # must be 0

# 2. Check mesh topology
admesh --no-fix part.stl
# Look for: 0 unconnected edges, 0 degenerate facets

# 3. Visual sanity check
DISPLAY=:0 openscad --render --imgsize=1280,960 \
  --camera=0,0,0,55,0,25,120 -o preview.png part.scad
```

If warnings appear, the most common fixes are:
- Add 0.1 mm overlap to eliminate coplanar faces.
- Ensure all `difference()` cutters extend past the body surface.
- Check for zero-thickness geometry (e.g., a pocket exactly as deep as the wall).
