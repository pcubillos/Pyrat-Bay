# Copyright (c) 2016-2019 Patricio Cubillos and contributors.
# Pyrat Bay is currently proprietary software (see LICENSE).

"""Cloud models."""

from .rayleigh import *

__all__ = rayleigh.__all__ + ['get_model']

def get_model(name):
    """Get a Rayleigh model by its name."""
    if name.startswith('dalgarno_'):
        mol = name.split('_')[1]
        return Dalgarno(mol)
    if name == 'lecavelier':
        return Lecavelier()


# Clean up top-level namespace--delete everything that isn't in __all__
# or is a magic attribute, and that isn't a submodule of this package
for varname in dir():
    if not ((varname.startswith('__') and varname.endswith('__')) or
            varname in __all__ ):
        del locals()[varname]
del(varname)
