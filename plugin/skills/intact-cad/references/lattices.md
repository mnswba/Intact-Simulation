# Implicit TPMS lattices

Use `build_tpms` for gyroid, schwarz_p, diamond, neovius, lidinoid or split_p. These are sampled nodal approximations of periodic implicit functions, clipped and capped inside box, cylinder (+Z), or sphere envelopes. They are not analytically exact minimal surfaces.

For example: `build_tpms(family="gyroid", length=30, width=30, height=30, cell_size=10, band=0.35, samples_per_cell=24)` creates a sheet lattice. `mode="solid"` retains F >= level; sheet mode retains |F-level| <= band. `phase_x/y/z` rotate the periodic phase in degrees, not the part. `gradient` varies sheet band along Z; it is not a mechanical optimization.

`band` and `level` are dimensionless. **Do not label band as mm wall thickness.** Implicit bands are not constant-thickness distance offsets. If the user requires exact wall thickness, explain this limit before presenting the lattice as meeting that requirement. Measured `relative_density` is the actual validated mesh volume divided by envelope volume; it is not a prescribed homogenized property. Validate load, flow, printing and minimum walls separately.

All numeric parameters remain in `program.parameters`; use `update_parameters` to change dimensions, band, level, phase, gradient or sampling, preserving revision guards. Change family/mode/envelope by revising the source while preserving other geometry. For custom/mixed assemblies, use the helper directly:

```python
import build123d as bd
from intact_lattice import tpms
def build(params):
    return {
        'lattice': tpms('gyroid', size=(params['length'],20,20),
                        cell_size=params['cell_size'], band=params['band'],
                        samples_per_cell=20),
        'base': bd.Pos(0,0,-11)*bd.Box(params['length'],20,2),
    }
```

The engine checks watertightness, winding, positive volume and finite vertices. All parts of mixed assemblies export as assembled triangle geometry. STEP is deliberately unavailable whenever a lattice mesh is present; return STL, GLB or 3MF links and standalone Python instead. Native faces/edges exist only for B-rep parts, and mesh picks remain approximate. Do not invent CAD face references for lattice triangles.

Sampling is limited to 2.5 million grid samples and 1.2 million combined preview triangles. Samples per cell is an integer 12–64; increase sampling for small details, but compare at two resolutions when dimensional accuracy matters. A budget error means reduce cell count/resolution or split the study, never disable isolation or silently replace the lattice with a box. Cell size is 0.1–1000 mm; envelopes are positive and at most 1000 mm per axis. `band` is 0.03–3; `level` is ±12; sheet gradient is ±0.9. A level that removes all material must fail without changing the saved model.

After generation, call `validate_model`, inspect a real snapshot and disclose family, mode, cell size, resolution, measured relative density and mesh-export scope. A valid closed mesh does not establish printability, a simulation result, or certification.

Equation reference: [nTop's published TPMS functions](https://support.ntop.com/hc/en-us/articles/360053267814-What-equations-are-used-to-create-the-TPMS-types).
