# Copyright (c) 2016-2019 Patricio Cubillos and contributors.
# Pyrat Bay is currently proprietary software (see LICENSE).

import os
import re
import sys
import setuptools
from setuptools import setup, Extension

from numpy import get_include

sys.path.append('pyratbay')
import VERSION as v
version = "{:d}.{:d}.{:d}".format(v.PBAY_VER, v.PBAY_MIN, v.PBAY_REV)

srcdir = 'src_c/'          # C-code source folder
incdir = 'src_c/include/'  # Include filder with header files

cfiles = os.listdir(srcdir)
cfiles = list(filter(lambda x:     re.search('.+[.]c$',     x), cfiles))
cfiles = list(filter(lambda x: not re.search('[.#].+[.]c$', x), cfiles))

inc = [get_include(), incdir]
eca = ['-ffast-math']
ela = []

extensions = []
for cfile in cfiles:
    e = Extension('pyratbay.lib.' + cfile.rstrip('.c'),
        sources=['{:s}{:s}'.format(srcdir, cfile)],
        include_dirs=inc,
        extra_compile_args=eca,
        extra_link_args=ela)
    extensions.append(e)

with open('README.md', 'r') as f:
    readme = f.read()

setup(name         = "pyratbay",
      version      = version,
      author       = "Patricio Cubillos",
      author_email = "patricio.cubillos@oeaw.ac.at",
      url          = "https://github.com/pcubillos/pyratbay",
      packages     = setuptools.find_packages(),
      install_requires = ['numpy>=1.8.1',
                          'scipy>=0.13.3',
                          'matplotlib>=1.3.1',
                          'sympy>=0.7.6',
                          'mc3>=3.0.0rc2',
                         ],
      tests_require = ['pytest>=3.9',],
      license      = "GNU GPLv2",
      description  = "Python Radiative Transfer in a Bayesian Framework.",
      long_description=readme,
      long_description_content_type="text/markdown",
      include_dirs = inc,
      entry_points={"console_scripts": ['pbay = pyratbay.__main__:main']},
      ext_modules  = extensions)
