#!/usr/bin/env python

# Copyright (c) 2016 Patricio Cubillos and contributors.
# Pyrat Bay is currently proprietary software (see LICENSE).

import sys, os
import numpy as np
import scipy.constants as sc

# Amagat (in molecules cm^-3):
N0 = sc.physical_constants[
        "Loschmidt constant (273.15 K, 101.325 kPa)"][0] * 1e-6

def speciesname(filename):
  """
  Extract the species name from filename.
  """
  sname = os.path.basename(filename).split("_")[0].split("-")
  name = ""
  for s in sname:
    i = 0
    while (s[i].isdigit()):
      i += 1
    name += s[i:]
  return name


def main():
  """
  Format Exomol's cross-section data file for pyrat.

  Examples
  --------
  $ ./CSformat_ExoMol.py 12C-1H4_200*.sigma

  Notes
  -----
  Download Exomol xsec tabulated data from:
    http://www.exomol.com/data/data-types/xsec
  You will need to download one temperature at a time.
  Keep dnu, nu_min, and nu_max fixed for each temperature.
  Be sure to check the Two-column output option.
  """

  # Parse arguments:
  filein = sys.argv[1:]
  # Number of temperatures (one temp sample per file):
  ntemp = nfiles = len(filein)

  # Array of sampled temperatures:
  temp = np.zeros(ntemp, np.double)

  # Read and extract data from files:
  for j in np.arange(nfiles):
    f = open(filein[j], "r")
    lines = f.readlines()
    f.close()

    if j == 0:
      # Number of wavenumber samples:
      nwave = len(lines)
      wn = np.zeros(nwave, np.double)
      # Allocate output data array:
      data = np.zeros((nwave,ntemp), np.double)
      species = speciesname(filein[j])

    # Extract temperature from the filename:
    temp[j] = (os.path.basename(filein[j]).split("_")[2])[:-1]
    if (j != 0) and (temp[j] < temp[j-1]):
      print("Error: The files must be sorted in increasing-temperature order.")
      return

    for i in np.arange(nwave):
      val = lines[i].split()
      # Get the wavenumber only if thi is the first file:
      if j == 0:
        wn[i]   = val[0]
      # Get the opacity:
      data[i,j] = val[1]

  # Convert units from cm2 molecule-1 to cm-1 amagat-1:
  data *= N0


  # Write to the output file:
  fileout = "ExoMol_{:s}_{:.1f}-{:.1f}cm-1_{:04d}-{:04d}K.dat".format(
                     species, wn[0], wn[-1], int(temp[0]), int(temp[-1]))
  fout = open(fileout, "w")

  # Write comments:
  fout.write("# This file contains the tabulated Exomol data for {:s}.\n"
             "#  (http://www.exomol.com/data/data-types/xsec)\n\n".
              format(species))
  # Write header:
  fout.write("@SPECIES\n{:s}\n\n".format(species))
  fout.write("@TEMPERATURES\n         ")
  for j in np.arange(len(temp)):
      fout.write("      {:4.0f}".format(temp[j]))
  fout.write("\n\n")

  # Write the data:
  fout.write("# Wavenumber in cm-1, CIA coefficients in cm-1 amagat-1:\n")
  fout.write("@DATA\n")
  for i in np.arange(nwave):
    fout.write(" {:7.1f} ".format(wn[i]))
    for j in np.arange(ntemp):
      fout.write(" {:.3e}".format(data[i,j]))
    fout.write("\n")

  fout.close()


if __name__ == "__main__":
  main()
