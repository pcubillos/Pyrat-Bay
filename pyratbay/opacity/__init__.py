# Copyright (c) 2021-2023 Patricio Cubillos
# Pyrat Bay is open-source software under the GPL-2.0 license (see LICENSE)

__all__ = [
    'broadening',
    'linelist',
    'partitions',
    'rayleigh',
]

from . import broadening
from . import linelist
from . import partitions
from . import rayleigh
from .lread import *
from .hydrogen_ion import *

from .. import version as ver

__all__ += hydrogen_ion.__all__ + lread.__all__

# Lineread version:
__version__ = f'{ver.LR_VER}.{ver.LR_MIN}.{ver.LR_REV}'


# Clean up top-level namespace--delete everything that isn't in __all__
# or is a magic attribute, and that isn't a submodule of this package
for varname in dir():
    if not ((varname.startswith('__') and varname.endswith('__')) or
            varname in __all__):
        del locals()[varname]
del(varname)
