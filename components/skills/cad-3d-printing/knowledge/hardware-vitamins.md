# Hardware Vitamins Database

Reference dimensions for components we design around. All values in mm.
Sources: official datasheets, mechanical drawings, and physical measurement.

---

## Pi Camera Module 3 (Standard)

Source: [RPi CM3 Mechanical Drawing](https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf)

| Property | Value | Notes |
|----------|-------|-------|
| PCB width | 25.0 | Along long edge |
| PCB height | 24.0 | Along short edge (FPC connector edge) |
| PCB thickness | 1.0 | Green PCB only |
| Total height | 11.5 | PCB to top of autofocus motor |
| Lens barrel diameter | ~8.5 | Autofocus unit, approximate |
| Lens barrel height | ~6.5 | Above PCB surface |
| Sensor pad | compressible | Lens module sits on squishy pad, can shift ~0.5mm |
| FPC connector | centered on 24mm edge | 15-pin, 1.0mm pitch |
| FPC ribbon width | ~15.0 | At camera end |
| Mounting holes | none | Board has no screw holes, use ledge/friction mount |

### Lens Position

**The lens barrel is NOT precisely centered on the PCB.** The autofocus module sits on a compressible rubber pad and can shift slightly (~0.5mm). From the mechanical drawing:

- Nominal center: approximately 12.5mm from each long edge, 12.0mm from each short edge
- Actual offset: variable due to pad compliance, estimated ~0.5-1.0mm toward FPC edge
- **Design rule: use aperture diameter >= lens barrel + 5mm clearance** (i.e., >= 14mm) to prevent any contact with the lens regardless of offset

### FPC Cable Details

- Camera-end connector: 15-pin, 1.0mm pitch, centered on 24mm PCB edge
- Cable width: ~15mm
- Cable exits perpendicular to PCB surface, bends 90 degrees
- Minimum bend radius: ~3mm (don't force tighter)
- Standard-Mini adapter cable: 200mm length for Pi 5

---

## Raspberry Pi 5

Source: [RPi 5 Mechanical Drawing](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf)

| Property | Value | Notes |
|----------|-------|-------|
| Board size | 85.0 x 56.0 | Standard Pi form factor |
| Height with components | ~20.0 | Including tallest connector |
| CSI connector | mini CSI-2 (22-pin, 0.5mm pitch) | Between Ethernet and USB-A ports |
| CSI connector position | ~12mm from board edge | On the Ethernet/USB side |
| Mounting holes | M2.5, 4 corners | 58mm x 49mm spacing |

---

## Common Fasteners

| Type | Thread | Head dia | Head height | Hole for clearance | Hole for tap |
|------|--------|----------|-------------|-------------------|-------------|
| M2 | 2.0 | 3.8 | 1.3 | 2.4 | 1.8 |
| M2.5 | 2.5 | 4.5 | 1.5 | 3.0 | 2.2 |
| M3 | 3.0 | 5.5 | 1.8 | 3.4 | 2.7 |

### Heat-Set Inserts (for PETG/ABS)

| Size | Insert OD | Insert length | Pocket diameter | Pocket depth |
|------|-----------|---------------|-----------------|-------------|
| M2 | 3.2 | 3.0 | 3.0 | 3.2 |
| M2.5 | 4.0 | 4.0 | 3.8 | 4.2 |
| M3 | 4.6 | 5.0 | 4.4 | 5.2 |
