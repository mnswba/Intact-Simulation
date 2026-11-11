"""Sampled TPMS sheet, not exact smooth STEP or a constant-thickness claim."""
import intact_lattice

def build(params):
    size=params['size']
    lattice=intact_lattice.tpms(family='gyroid',size=(size,size,size),cell_size=params['cell_size'],band=params['band'],samples_per_cell=params['samples_per_cell'])
    return {'gyroid':lattice}
