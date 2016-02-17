import sys, os
import traceback
import textwrap
import struct
import numpy as np

from .. import constants as pc

"""
Pyrat tools: Tools for the Pyrat-Bay project.
"""

def parray(string):
  """
  Convert a string containin a list of white-space-separated (and/or
  newline-separated) values into a numpy array
  """
  if string == 'None':
    return None
  try:    # If they can be converted into doubles, do it:
    return np.asarray(string.split(), np.double)
  except: # Else, return a string array:
    return string.split()


def exit(comm=None, abort=False, message=None, comm2=None):
  """
  Stop execution.

  Parameters:
  -----------
  comm: MPI communicator
     An MPI Intracommunicator.
  abort: Boolean
     If True send (gather) an abort flag integer through comm.
  message: String
     Print message on exit.

  Modification History:
  ---------------------
  2014-04-20  patricio  Initial implementation (extracted from transit project).
  """
  if message is not None:
    print(message)
  if comm is not None:
    if abort:
      #comm_gather(comm, np.array([1], dtype='i'), MPI.INT)
      pass
    comm.Barrier()
    comm.Disconnect()
  if comm2 is not None:
    comm2.Barrier()
    comm2.Disconnect()
  sys.exit(0)


def error(message, lev=-2):
  """
  Pretty print error message.
  """
  # Trace back the file, function, and line where the error source:
  t = traceback.extract_stack()
  # Extract fields:
  efile = t[lev][0]
  efile = efile[efile.rfind('/')+1:]
  efunc = t[lev][2]
  eline = t[lev][1]
  # Indent and wrap message to 70 characters:
  msg = textwrap.fill(message, initial_indent   ="    ",
                               subsequent_indent="    ")
  # Print it out:
  print(
    "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n"
    "  Error in module: '%s', function: '%s', line: %d\n"
    "%s\n"
    "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n"%
    (efile, efunc, eline, msg))
  sys.exit(0)


def warning(message):
  """
  Print message surrounded by colon bands.

  Modification History:
  ---------------------
  2014-06-15  patricio  Initial implementation.
  """
  print(
    "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n"
    "  Warning:")
  msg(1, message, 4)
  print(
    "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n")


def msg(verblevel, message, indent=0, si=None):
  """
  Conditional message printing to screen.

  Parameters:
  -----------
  verblevel: Integer
     If positive, print the given message.
  message: String
     Message to print.
  indent: Integer
     Number of blank spaces for indentation.
  si: Integer
     Subsequent indentation.  If None, keep indent as the subsequent
     indentation.
  """
  if verblevel <= 0:
    return

  sentences = message.splitlines()
  # Set indentation string:
  indspace = " "*indent
  if si is None:
    sindspace = indspace
  else:
    sindspace = " "*si

  for s in sentences:
    msg = textwrap.fill(s, replace_whitespace=True,
                        initial_indent=indspace, subsequent_indent=sindspace)
    print(msg)


def binsearch(dbfile, wavelength, rec0, nrec, upper=True):
  """
  Do a binary search in TLI dbfile for record that has wavelength iwl

  Parameters:
  -----------
  dbfile: File object
     TLI file where to search.
  wavelength: Scalar
     Target wavelength.
  rec0: Integer
     Position of first record.
  nrec: Integer
     Number of records.
  upper: Boolean
     Wavelength is an upper boundary, return the index of value smaller
     than wavelength.

  Returns:
  --------
  Index of record with

  Modification History:
  ---------------------
  2013        madison   Initial implementation.
  2014-03-05  patricio  Added documentation, updated Madison's code, and
                        included searchup parameter. pcubillos@fulbrightmail.org
  2014-06-22  patricio  Adapted from pylineread project to read from TLI.
  2014-08-03  patricio  Added boundaries condition in sequential search.
  """
  # Wavelength of record:
  ilo = 0
  ihi = nrec

  # Start binary search:
  while ihi - ilo > 1:
    # Middle record index:
    irec = (ihi + ilo)/2

    # Read wavelength from TLI file record:
    dbfile.seek(irec*pc.dreclen + rec0, 0)
    rec_wl = struct.unpack('d', dbfile.read(8))[0]
    # Update search limits:
    if rec_wl > wavelength:
      ihi = irec
    else:
      ilo = irec
  #print("Binary found:      %.7f (%d)"%(rec_wl, irec))

  # Sequential search:
  if rec_wl < wavelength:
    jump =  1 # Move up
  else:
    jump = -1 # Move down

  dbfile.seek(irec*pc.dreclen + rec0, 0)
  next_wl = struct.unpack('d', dbfile.read(8))[0]
  while (np.sign(next_wl-wavelength) == np.sign(rec_wl-wavelength)):
    irec += jump
    # Check for boundaries:
    if (irec < 0 or irec > nrec):
      return np.clip(irec, 0, nrec)
    dbfile.seek(irec*pc.dreclen + rec0, 0)
    rec_wl  = next_wl
    next_wl = struct.unpack('d', dbfile.read(8))[0]
  #print("Sequential found:  %.7f"%next_wl)

  # Return the index withing the boundaries:
  return irec - (jump+upper)/2


def pprint(array, precision=3, fmt=None):
  """
  Pretty print a Numpy array.  Set desired precision and format, and
  remove line break from the string output.

  Parameters:
  -----------
  array: 1D ndarray
     Array to be pretty printed.
  precision: Integer
     Precision for floating point values.
  fmt: format
     Numeric format.

  Modification History:
  ---------------------
  2015-01-25  patricio  Initial implementation.
  """
  default_prec = np.get_printoptions().get('precision')
  np.set_printoptions(precision=precision)

  # Pretty array is a copy of array:
  parray = np.copy(array)
  if format is not None:
    parray = np.asarray(array, fmt)

  # Convert to string and remove line-breaks:
  sarray = str(array).replace("\n", "")
  np.set_printoptions(precision=default_prec)
  return sarray


def divisors(number):
  """
  Find all the integer divisors of number.
  """
  divs = []
  for i in np.arange(1, number/2+1):
    if number % i == 0:
      divs.append(i)
  divs.append(number)
  return np.asarray(divs, np.int)


def unpack(file, n, dtype):
  """
  Wrapper for struct unpack.

  Parameters:
  -----------
  file: File object
     File object to read from.
  n: Integer
     Number of elements to read from file.
  dtype: String
     Data type of the bytes read.

  Returns:
  --------
  output: Scalar, tuple, or string
     If dtype is 's' return the string.
     If there is a single element to read, return the scalar value.
     Else, return a tuple with the elements read.
  """
  # Compute the reading format:
  fmt  = "{:d}{:s}".format(n, dtype)
  # Calculate the number of bytes to read:
  size = struct.calcsize(fmt)
  # Read:
  output = struct.unpack(fmt, file.read(size))
  # Return:
  if (n == 1) or (dtype == "s"):
    return output[0]
  else:
    return output


def u(units):
  """
  Get the conversion factor (to the CGS system) for units.

  Parameters:
  -----------
  units: String
     Name of units
  """
  # Accept only valid units:
  if units not in ["eV",  "A", "nm", "um", "mm", "cm", "m", "km", "au", "pc",
                   "mbar", "bar", "kelvin", "amu", "amagat"]:
    # Throw error:
    error("Units name '{:s}' does not exist.".format(units), lev=-3)
  exec("factor = pc.{:s}".format(units))
  return factor
