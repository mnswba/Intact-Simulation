"""Original Intact TPMS showcase. CAD coordinates in mm; nodal sampled mesh."""
from intact_lattice import tpms
def build(params):
    return {'gradient_gyroid_core':tpms('gyroid',size=(params['sx'],params['sy'],params['sz']),cell_size=params['cell'],band=params['band'],samples_per_cell=int(params['samples']),envelope='box',gradient=params['gradient'],phase=[0, 0, 0])}
