# Copyright (c) 2016-2020 Patricio Cubillos.
# Pyrat Bay is open-source software under the GNU GPL-2.0 license (see LICENSE).

import os
import pytest

import numpy as np

import pyratbay.broadening as pb
import pyratbay.constants  as pc

os.chdir(pc.ROOT + 'tests')

keys = ['lorentz', 'gauss',
        'voigt0.01', 'voigt0.1', 'voigt1.0', 'voigt10.0', 'voigt100.0']
expected = {key:np.load("expected_profile_{:s}_test.npz".
                        format(key))['arr_0']
            for key in keys}


def test_Lorentz_hwhm():
    lor = pb.Lorentz(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-10.0, 10.0, 100001)
    np.testing.assert_approx_equal(
        0.5*np.ptp(x[lor(x)>0.5*np.amax(lor(x))]), 1.0, 3)


def test_Lorentz_integral():
    lor = pb.Lorentz(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-1000.0, 1000.0, 100001)
    np.testing.assert_approx_equal(np.trapz(lor(x),x), 1.0, 3)


def test_Lorentz():
    lor = pb.Lorentz(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-10.0, 10.0, 1001)
    np.testing.assert_allclose(lor(x), expected['lorentz'], rtol=1e-7)


def test_Gauss_hwhm():
    gauss = pb.Gauss(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-10.0, 10.0, 100001)
    np.testing.assert_approx_equal(
        0.5*np.ptp(x[gauss(x)>0.5*np.amax(gauss(x))]), 1.0, 3)


def test_Gauss_integral():
    gauss = pb.Gauss(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-100.0, 100.0, 100001)
    np.testing.assert_approx_equal(np.trapz(gauss(x),x), 1.0, 7)


def test_Gauss():
    gauss = pb.Gauss(x0=0.0, hwhm=1.0, scale=1.0)
    x = np.linspace(-5.0, 5.0, 1001)
    np.testing.assert_allclose(gauss(x), expected['gauss'], rtol=1e-7)


@pytest.mark.parametrize("hL, key",
    [(0.01,  'voigt0.01'),
     (0.1,   'voigt0.1'),
     (1.0,   'voigt1.0'),
     (10.0,  'voigt10.0'),
     (100.0, 'voigt100.0')])
def test_Voigt(hL, key):
    Nw = 10.0
    hG = 1.0
    voigt = pb.Voigt(x0=0.0, hwhmG=hG, hwhmL=hL)
    width = 0.5346*hL + np.sqrt(0.2166*hL**2+hG**2)
    x = np.arange(-Nw*width, Nw*width, width/300.0)
    np.testing.assert_allclose(voigt(x), expected[key], rtol=1e-7)


def test_min_widths():
    min_temp = 500.0     # Kelvin
    max_temp = 2500.0  # Kelvin
    min_wn   = 1.0/(0.6*pc.um)
    max_mass = 27.02534  # HCN molecular mass (amu)
    min_rad  = 2.5 * pc.A
    min_press = 1e-5 * pc.bar
    dmin, lmin = pb.min_widths(min_temp, max_temp, min_wn, max_mass,
                               min_rad, min_press)
    np.testing.assert_allclose(dmin, 0.025672743788107903)
    np.testing.assert_allclose(lmin, 3.9945391902150206e-07)


def test_max_widths():
    min_temp =  500.0  # Kelvin
    max_temp = 2500.0  # Kelvin
    max_wn   = 1.0/(12.0*pc.um)
    min_mass = 1.007940  # H molecular mass (amu)
    max_rad  = 2.89/2.0 * pc.A
    max_press = 100 * pc.bar
    dmax, lmax = pb.max_widths(min_temp, max_temp, max_wn, min_mass,
                               max_rad, max_press)
    np.testing.assert_allclose(dmax, 0.01486262554305687)
    np.testing.assert_allclose(lmax, 8.009255370607491)

