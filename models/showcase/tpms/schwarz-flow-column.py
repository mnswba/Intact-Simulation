"""Original Intact TPMS showcase. CAD coordinates in mm; nodal sampled mesh."""
from intact_lattice import tpms
def build(params):
    return {'schwarz_flow_column':tpms('schwarz_p',size=(params['sx'],params['sy'],params['sz']),cell_size=params['cell'],band=params['band'],samples_per_cell=int(params['samples']),envelope='cylinder',gradient=params['gradient'],phase=[0, 0, 0])}
