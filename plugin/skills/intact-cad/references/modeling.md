# Tested build123d 0.13 patterns

All sources define `build(params)` and return named solids. Choose geometry from the requested design; these examples are API guidance. Fifty evaluated families include extrusions, fillets, revolutions, mixed-profile lofts, curved/helical sweeps, text, thin features and multipart assemblies.

## Bores and explicit parameters

```python
import build123d as bd
def build(params):
    plate = bd.Box(params['length'], params['width'], params['thickness'])
    bore = bd.Cylinder(params['bore']/2, params['thickness']+2)
    return {'plate': plate-bore}
```

Primitives center by default. State an explicit alignment or placement when a mating face must stay fixed. Extending a tool slightly beyond a face avoids accidental blind cuts. Rotations/positions multiply shapes: `bd.Pos(x,y,z) * bd.Rot(0,90,0) * bd.Cylinder(r,h)`. Confirm the resulting axis and through depth rather than inferring it from the tool's name.

## Revolved profile

```python
import build123d as bd
def build(params):
    r = params['radius']
    profile = bd.Plane.XZ * bd.Polygon(
        (5,0),(r,0),(r,3),(r-4,6),(r-4,14),(r,17),(r,20),(5,20),
        align=None)
    return {'pulley': bd.revolve(profile, axis=bd.Axis.Z)}
```

`align=None` preserves profile coordinates. A radius coordinate of 5 leaves a 10 mm center bore. An indexed tooth wheel with rectangular teeth is not an involute gear or a load-rated component.

## Lofted wall

```python
import build123d as bd
def build(params):
    h = params['height']
    outer = bd.loft([bd.Circle(25),bd.Plane.XY.offset(h)*bd.Circle(14)])
    inner = bd.loft([bd.Circle(23),bd.Plane.XY.offset(h)*bd.Circle(12)])
    return {'duct': outer-inner}
```

Keep inner/outer ends compatible; check that wall booleans leave valid positive-volume solids. A rectangle-to-circle loft is supported. For offsets, construct the upper plane at `bd.Plane(origin=(x,0,h))`.

## Curved and helical sweep

```python
import build123d as bd
def build(params):
    path = bd.Helix(params['pitch'],36,10)
    start = bd.Plane(origin=path.position_at(0),z_dir=path.tangent_at(0))
    return {'spring': bd.sweep(start*bd.Circle(params['wire']/2),path,is_frenet=True)}
```

The initial section plane must be normal to the path tangent. Check adjacent turns for self-intersection. Some fine helical features approach the worker's time/mesh budget; simplify the requested operation without silently deleting its defining geometry.

## Fillets, chamfers and sketches

Use native edge filters with a valid radius: `bd.fillet(body.edges().filter_by(bd.Axis.Y), radius)`. `bd.chamfer(..., length)` uses a length, not a fillet radius. Select edges by actual geometry or clearly established axes and dimensions. A failed fillet is a geometric constraint to resolve; reducing it needs to preserve the user's requirement or be explained.

Extrude closed sketches into solids. `bd.extrude(...)`, `bd.revolve(...)`, `bd.loft(...)` and `bd.sweep(...)` return Parts; builder contexts return their `.part`. Do not apply `.part` to an already returned Part or treat a sketch as a solid.

Text engraving can use `bd.Text(...,font_size=...,font='DejaVu Sans')`, extruded as a cutter and placed to penetrate the intended face. Native fonts must be available in the worker. Preserve the existing font and alignment during text-only edits.


## Bounds and editable dimensions

For generated parts, `part.params.length/width/height` are native bounding dimensions. Actual editable design values are `spec.program.parameters`. The schema retains template compatibility fields such as `finCount`, `holeDiameter` and `wall`; those default values are not measurements of a custom model. Use `measure_model` for native bounds/volume/area and native face references for individual radii; do not infer a model's fin count or bore from a compatibility default.
