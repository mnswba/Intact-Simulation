# Example models

These original, deterministic CAD programs demonstrate the same `build(params)` contract that an AI client uses. They are regression examples, not evidence of training model weights. All dimensions are millimeters.

After [runtime setup](../docs/install.md), run from the repository root:

```bash
uv run --project backend --extra cad --frozen python models/run.py flange
uv run --project backend --extra cad --frozen python models/run.py enclosure
uv run --project backend --extra cad --frozen python models/run.py gyroid
```

Or use `~/.local/share/intact-simulation/runtime/.venv/bin/python models/run.py flange` with the installed runtime. Exported files and local model state remain in ignored `outputs/examples/`. Use `--output PATH` for another directory; do not commit private outputs.

| Source | Parameters | Expected behavior |
| --- | --- | --- |
| [flange.py](flange.py) | 80 mm diameter, 8 mm thickness, 24 mm bore, six 6 mm holes on a 60 mm circle | One solid, analytic volume agreement; STEP/STL/GLB/3MF |
| [enclosure.py](enclosure.py) | 60 × 40 × 20 mm body, 2 mm walls/lid, 5 mm lid gap | Two solids, open cavity, assembled height 27 mm; STEP/STL/GLB/3MF |
| [gyroid.py](gyroid.py) | 24 mm envelope, 8 mm cells, 0.3 dimensionless band, 16 samples/cell | Valid sampled triangle solid; STL/GLB/3MF, no exact STEP |

Numeric defaults and export expectations are in [catalog.json](catalog.json). The runner checks positive volumes, part counts and analytical flange volume; native and lattice validity are additionally checked by the CAD engine. It does not certify wall thickness or simulate these parts.

In an AI conversation, supply the source and parameters to `build_model`, then inspect `measure_model`, `validate_model` and `snapshot_model`. Use design-specific checks for acceptance rather than accepting a plausible screenshot alone. For simulation, establish material properties, domains and boundary conditions first; see [simulation scope](../docs/simulation.md).
