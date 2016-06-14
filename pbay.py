#! /usr/bin/env python

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import pyratbay as pb


def main():
  """
  Pyrat Bay: Python Radiative Transfer in a Bayesian framework

  Notes
  -----
  This code is based on the Bayesian Atmospheric Radiative Transfer (BART)
  code, developed at UCF:  https://github.com/exosports/BART
  """
  pb.pbay.run(sys.argv, True)


if __name__ == "__main__":
  main()
