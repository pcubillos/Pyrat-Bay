# Copyright (c) 2021-2023 Patricio Cubillos
# Pyrat Bay is open-source software under the GPL-2.0 license (see LICENSE)

import ctypes
import multiprocessing as mp

import numpy as np

from .. import constants as pc
from .. import io as io
from ..lib import _extcoeff as ec


def compute_opacity(pyrat):
    """
    Compute the cross-sections spectum (cm2 molecule-1) over a tabulated
    grid of temperature, pressure, and wavenumber.
    """
    ex = pyrat.ex
    spec = pyrat.spec
    log = pyrat.log

    if ex.extfile is None:
        log.error(
            'Undefined output opacity file (extfile) needed to '
            'compute opacity table'
        )
    if len(ex.extfile) > 1:
        log.error(
            'Computing opacity table, but there is more than one'
            'output opacity file set (extfile)',
        )
    if ex.tmin is None:
        log.error(
            'Undefined lower temperature boundary (tmin) needed to '
            'compute opacity table',
        )
    if ex.tmax is None:
        log.error(
            'Undefined upper temperature boundary (tmax) needed to '
            'compute opacity table',
        )
    if ex.tstep is None:
        log.error(
            'Undefined temperature sampling step (tstep) needed to '
            'compute opacity table',
        )
    if pyrat.inputs.tlifile is None:
        log.error(
            'Undefined input TLI files (tlifile) needed to compute '
            'opacity table',
        )

    extfile = ex.extfile[0]
    log.head(f"\nGenerating new cross-section table file:\n  '{extfile}'")
    # Temperature boundaries check:
    if ex.tmin < pyrat.lbl.tmin:
        log.error(
            'Requested cross-section table temperature '
            f'(tmin={ex.tmin:.1f} K) below the lowest available TLI '
            f'temperature ({pyrat.lbl.tmin:.1f} K)'
        )
    if ex.tmax > pyrat.lbl.tmax:
        log.error(
            'Requested cross-section table temperature '
            f'(tmax={ex.tmax:.1f} K) above the highest available TLI '
            f'temperature ({pyrat.lbl.tmax:.1f} K)'
        )

    # Create the temperature array:
    ex.ntemp = int((ex.tmax-ex.tmin)/ex.tstep) + 1
    ex.temp = np.linspace(ex.tmin, ex.tmin + (ex.ntemp-1)*ex.tstep, ex.ntemp)

    imol = pyrat.lbl.mol_index[pyrat.lbl.mol_index>=0]
    ex.species = pyrat.atm.species[np.unique(imol)]
    ex.nspec = len(pyrat.ex.species)

    with np.printoptions(formatter={'float':'{:.1f}'.format}):
        log.msg(f"Temperature sample (K):\n {ex.temp}", indent=2)

    # Evaluate the partition function at the given temperatures:
    log.msg("Interpolate partition function.", indent=2)
    ex.z = np.zeros((pyrat.lbl.niso, ex.ntemp), np.double)
    for i in range(pyrat.lbl.niso):
        ex.z[i] = pyrat.lbl.iso_pf_interp[i](ex.temp)

    # Allocate wavenumber, pressure, and isotope arrays:
    ex.wn = spec.wn
    ex.nwave = spec.nwave
    ex.press = pyrat.atm.press
    ex.nlayers = pyrat.atm.nlayers

    # Allocate extinction-coefficient array:
    log.msg("Calculate cross-sections.", indent=2)
    size = ex.nspec * ex.ntemp * ex.nlayers * ex.nwave
    sm_ect = mp.Array(ctypes.c_double, np.zeros(size, np.double))
    ex.etable = np.ctypeslib.as_array(
        sm_ect.get_obj()).reshape((ex.nspec, ex.ntemp, ex.nlayers, ex.nwave))

    # Multi-processing extinction calculation (in C):
    processes = []
    indices = np.arange(ex.ntemp*ex.nlayers) % pyrat.ncpu  # CPU indices
    grid = True
    add = False
    for i in range(pyrat.ncpu):
        args = (pyrat, np.where(indices==i)[0], grid, add)
        proc = mp.get_context('fork').Process(target=extinction, args=args)
        processes.append(proc)
        proc.start()
    for proc in processes:
        proc.join()

    # Store values in file:
    io.write_opacity(extfile, ex.species, ex.temp, ex.press, ex.wn, ex.etable)
    log.head(
        f"Cross-section table written to file: '{extfile}'.",
        indent=2,
    )


def extinction(pyrat, indices, grid=False, add=False):
    """
    Python multiprocessing wrapper for the extinction-coefficient (EC)
    calculation function for the atmospheric layers or EC grid.

    Parameters
    ----------
    pyrat: Pyrat Object
    indices: 1D integer list
       The indices of the atmospheric layer or EC grid to calculate.
    grid: Bool
       If True, compute EC per species for EC grid.
       If False, compute EC for atmospheric layer.
    add: Bool
       If True, co-add EC contribution (cm-1) from all species.
       If False, keep EC contribution (cm2 molec-1) from each species separated.
    """
    atm = pyrat.atm
    if add:  # Total extinction coefficient spectrum (cm-1)
        extinct_coeff = np.zeros((1, pyrat.spec.nwave))
    else:  # Cross-section spectra for each species (cm2 molecule-1)
        extinct_coeff = np.zeros((pyrat.ex.nspec, pyrat.spec.nwave))

    # Get species indices in opacity table for the isotopes:
    iext = np.zeros(pyrat.lbl.niso, int)
    for i in range(pyrat.lbl.niso):
        mol_index = pyrat.lbl.mol_index[i]
        if mol_index != -1:
            iext[i] = np.where(
                pyrat.ex.species == pyrat.atm.species[mol_index])[0][0]
        else:
            iext[i] = -1  # Isotope not in atmosphere
            # FINDME: find patch for this case in ec.extinction()

    # Turn off verb of all processes except the first:
    verb = pyrat.log.verb
    pyrat.log.verb = (0 in indices) * verb

    for i,index in enumerate(indices):
        ilayer = index % atm.nlayers  # Layer index
        pressure = atm.press[ilayer]  # Layer pressure
        molq = atm.vmr[ilayer]  # Molecular abundance
        density = atm.d[ilayer]  # Molecular density
        if grid:  # Take from grid
            itemp = int(index / atm.nlayers)  # Temp. index in EC table
            temp = pyrat.ex.temp[itemp]
            iso_pf = pyrat.ex.z[:,itemp]
            pyrat.log.msg(
                "Extinction-coefficient table: "
                f"layer {ilayer+1:3d}/{atm.nlayers}, "
                f"iteration {i+1:3d}/{len(indices)}.",
                indent=2,
            )
        else: # Take from atmosphere
            temp = atm.temp[ilayer]
            iso_pf = pyrat.lbl.iso_pf[:,ilayer]
            pyrat.log.msg(
                f"Calculating extinction at layer {ilayer+1:3d}/{atm.nlayers} "
                f"(T={temp:6.1f} K, p={pressure/pc.bar:.1e} bar).",
                indent=2,
            )

        # Calculate extinction-coefficient in C:
        extinct_coeff[:] = 0.0
        interpolate_flag = int(
            pyrat.spec.resolution is not None
            or pyrat.spec.wlstep is not None
        )
        ec.extinction(
            extinct_coeff,
            pyrat.voigt.profile, pyrat.voigt.size, pyrat.voigt.index,
            pyrat.voigt.lorentz, pyrat.voigt.doppler,
            pyrat.spec.wn, pyrat.spec.own, pyrat.spec.odivisors,
            density, molq, pyrat.atm.mol_radius, pyrat.atm.mol_mass,
            pyrat.lbl.mol_index, pyrat.lbl.iso_mass, pyrat.lbl.iso_ratio,
            iso_pf, iext,
            pyrat.lbl.wn, pyrat.lbl.elow, pyrat.lbl.gf, pyrat.lbl.isoid,
            pyrat.voigt.cutoff, pyrat.ex.ethresh, pressure, temp,
            verb-10, int(add),
            interpolate_flag,
        )
        # Store output:
        if grid:   # Into grid
            pyrat.ex.etable[:, itemp, ilayer] = extinct_coeff
        elif add:  # Into ex.ec array for atmosphere
            pyrat.ex.ec[ilayer:ilayer+1] = extinct_coeff
        else:      # return single-layer EC of given layer
            return extinct_coeff


def get_ec(pyrat, layer):
    """
    Compute per-species extinction coefficient at requested layer.
    """
    # Line-by-line:
    exc = extinction(pyrat, [layer], grid=False, add=False)
    label = []
    for i in range(pyrat.ex.nspec):
        imol = np.where(pyrat.atm.species == pyrat.ex.species[i])[0][0]
        exc[i] *= pyrat.atm.d[layer,imol]
        label.append(pyrat.atm.species[imol])
    return exc, label
