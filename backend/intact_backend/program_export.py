"""Make a generated CAD source download executable outside the plugin."""
def executable_source(source:str,parameters:dict,imported:bool=False,colors:dict|None=None,meshing:dict|None=None)->str:
    from pathlib import Path
    lattice_bootstrap=''
    if 'intact_lattice' in source:
        helper=Path(__file__).with_name('intact_lattice.py').read_text()
        lattice_bootstrap='import sys as _sys, types as _types\n_lattice_module = _types.ModuleType("intact_lattice")\nexec('+repr(helper)+', _lattice_module.__dict__)\n_sys.modules["intact_lattice"] = _lattice_module\n'
    prefix='''import build123d as bd
from pathlib import Path
# Keep input.step next to this script (download it from Intact).
_input = bd.import_step(Path(__file__).with_name('input.step'))
imported_parts = {}
def _collect(s):
    import re
    if s.children:
        for child in s.children: _collect(child)
    elif s.solids():
        key = re.sub('[^a-z0-9_]+', '_', s.label.lower()).strip('_')[:40] or 'part'
        if not key[0].isalpha(): key = 'part_' + key
        base = key; n = 2
        while key in imported_parts: key = f'{base}_{n}'; n += 1
        imported_parts[key] = s
_collect(_input)
input_shape = _input
''' if imported else ''
    if imported=='stl':prefix='import trimesh\nfrom pathlib import Path\nfrom intact_lattice import MeshPart\ninput_mesh = MeshPart(trimesh.load(Path(__file__).with_name("input.stl"), force="mesh", process=True))\n'
    linear=(meshing or {}).get('linear_deflection_mm',.001)
    angular=(meshing or {}).get('angular_deflection_rad',.1)
    result=lattice_bootstrap+prefix+source+'\n\n'+'''# Requires build123d 0.13; TPMS also requires trimesh and scikit-image.
if __name__ == "__main__":
    import build123d as bd
    from copy import deepcopy
    import sys
    params = '''+repr(parameters)+'''
    result = build(params)
    if isinstance(result, bd.BuildPart):
        result = result.part
    if isinstance(result, dict):
        shapes = []
        for name, shape in result.items():
            shape = shape.part if isinstance(shape, bd.BuildPart) else shape
            shape = deepcopy(shape)
            shape.label = name
            shapes.append(shape)
    elif isinstance(result, (list, tuple)):
        shapes = []
        for index, shape in enumerate(result):
            shape = shape.part if isinstance(shape, bd.BuildPart) else shape
            shape = deepcopy(shape)
            shape.label = f"part_{index+1}"
            shapes.append(shape)
    else:
        result.label = "model"
        shapes = [result]
    saved_colors = '''+repr(colors or {})+'''
    if "intact_lattice" in sys.modules and any(isinstance(shape, sys.modules["intact_lattice"].MeshPart) for shape in shapes):
        from intact_lattice import MeshPart, write_mesh_exports
        import numpy as np, trimesh
        items = []
        for shape in shapes:
            if isinstance(shape, MeshPart):
                mesh = shape.mesh
            else:
                points, triangles = shape.tessellate(0.05)
                mesh = trimesh.Trimesh(np.array([tuple(p) for p in points]), np.array(triangles))
            items.append((shape.label, mesh, saved_colors.get(shape.label, "#6287bc")))
        write_mesh_exports(items, ".")
        raise SystemExit(0)
    for shape in shapes:
        if shape.label in saved_colors:
            shape.color = bd.Color(saved_colors[shape.label])
        elif shape.color is None:
            shape.color = bd.Color("#6287bc")
    model = bd.Compound(children=[s.part if isinstance(s, bd.BuildPart) else s for s in shapes])
    bd.export_step(model, "model.step")
    bd.export_stl(model, "model.stl", tolerance=0.001)
    bd.export_gltf(model, "model.glb", binary=True, linear_deflection=0.1)
    mesher = bd.Mesher()
    mesher.add_shape(model, linear_deflection=0.1)
    mesher.write("model.3mf")
'''

    return result.replace('tolerance=0.001','tolerance='+repr(linear)+', angular_tolerance='+repr(angular)).replace('linear_deflection=0.1','linear_deflection='+repr(linear))
