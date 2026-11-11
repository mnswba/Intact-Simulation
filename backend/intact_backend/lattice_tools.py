"""Validated TPMS tool arguments compiled to ordinary editable CAD source."""
from .intact_lattice import FAMILIES

def build_tpms(projects,args,cancel_event=None):
    values=dict(args)
    family=values.pop('family','gyroid');mode=values.pop('mode','sheet');envelope=values.pop('envelope','box')
    if family not in FAMILIES or mode not in ('sheet','solid') or envelope not in ('box','cylinder','sphere'):raise ValueError('Unsupported TPMS family, mode or envelope.')
    control={key:values.pop(key,None) for key in ('model_id','expected_revision','name')}
    defaults={'length':30,'width':30,'height':30,'cell_size':10,'band':.3,'level':0,'samples_per_cell':20,'phase_x':0,'phase_y':0,'phase_z':0,'gradient':0}
    if set(values)-set(defaults):raise ValueError('Unknown lattice parameter.')
    defaults.update(values)
    source="from intact_lattice import tpms\ndef build(params):\n    return {'lattice': tpms(family="+repr(family)+", mode="+repr(mode)+", envelope="+repr(envelope)+", size=(params['length'],params['width'],params['height']), cell_size=params['cell_size'], band=params['band'], level=params['level'], samples_per_cell=params['samples_per_cell'], phase=(params['phase_x'],params['phase_y'],params['phase_z']), gradient=params['gradient'])}\n"
    return projects.build(source,defaults,name=control['name'] or family.replace('_',' ').title()+' TPMS',model_id=control['model_id'],expected_revision=control['expected_revision'],cancel_event=cancel_event)
