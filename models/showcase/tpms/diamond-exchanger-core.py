"""Original Intact TPMS showcase. CAD coordinates in mm; nodal sampled mesh."""
from intact_lattice import tpms
def build(params):
    return {'diamond_exchanger_core':tpms('diamond',size=(params['sx'],params['sy'],params['sz']),cell_size=params['cell'],band=params['band'],samples_per_cell=int(params['samples']),envelope='box',gradient=params['gradient'],phase=[15, 15, 0])}
