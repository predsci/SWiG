#!/usr/bin/env python3
import numpy as np
import argparse
#
import psi_io as ps

# E-SWiM:  Empirical Solar Wind Models
#
# Authors:
#           Savir Basil
#           Ronald M. Caplan
#           Jon A. Linker
#
# Version 2.0.0
#
########################################################################
#        Predictive Science Inc.
#        www.predsci.com
#        San Diego, California, USA 92121
########################################################################
# Copyright 2024 Predictive Science Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########################################################################

def argParsing():

    parser = argparse.ArgumentParser(description='Compute Empirical Solar Wind Models (SWiM)')

    ## Input file names

    parser.add_argument("-dchb", type=str, 
                        help='Distance to coronal hole boundaries (DCHB) hdf5 filename.',
                        required=True)
    parser.add_argument("-expfac", type=str, 
                        help='Expansion factor hdf5 filename.',
                        required=True)

    ## Model type selected

    parser.add_argument("-model", type=str,
                        help='Model type. Allowed model types are: wsa, wsa2, psi',
                        required=True)

    ## Parameters for both the WSA and PSI/DCHB model

    parser.add_argument("-vslow", type=float,
                        required=False,
                        help='Slow wind speed [km/s]')
    parser.add_argument("-vfast", type=float,
                        required=False,
                        help='Fast wind speed [km/s]')

    ## Parameters unique to the WSA model

    parser.add_argument("-vmax", type=float,
                        required=False,
                        help='Maximum wind speed [km/s] (Only used in wsa model)')
    parser.add_argument("-c1", type=float,
                        required=False,
                        help='Expansion factor power')
    parser.add_argument("-c2", type=float,
                        required=False,
                        help='CH distance multiplier')
    parser.add_argument("-c3_i", type=float,
                        required=False,
                        help='CH distance factor (inverse of C3 in CORHEL6 interface).')
    parser.add_argument("-c4", type=float,
                        required=False,
                        help='CH distance power')
    parser.add_argument("-c5", type=float,
                        required=False,
                        help='Overall power for term involving DCHB.')

    ## Parameters unique to the PSI DCHB model

    parser.add_argument("-psi_eps", type=float,
                        required=False,
                        help='CH distance parameter')
    parser.add_argument("-psi_width", type=float,
                        required=False,
                        help='CH distance width')

    ## Parameters for the density and temperature

    parser.add_argument("-rhofast", type=float,
                        default=152.0,
                        required=False,
                        help='Fast wind density  [#/cm3]')
    parser.add_argument("-tfast", type=float,
                        default=1.85e6,
                        required=False,
                        help='Fast wind temperature [K]')

    return parser.parse_args()

def main():

    ## Get iinput arguments:
    args = argParsing()

    ## Set defaults based on model:
    if args.model == 'wsa':
      if (args.vslow is None):
        args.vslow = 250.0
      if (args.vfast is None):
        args.vfast = 680.0
      if (args.vmax is None):
        args.vmax = 800.0
      if (args.c1 is None):
        args.c1 = 1.0/3.0
      if (args.c2 is None):
        args.c2 = 0.8
      if (args.c3_i is None):   #INVERSE of new interface
        args.c3_i = 0.25
      if (args.c4 is None):
        args.c4 = 4.0
    elif args.model == 'wsa2':
      if (args.vslow is None):
        args.vslow = 285.0
      if (args.vfast is None):
        args.vfast = 625.0
      if (args.c1 is None):
        args.c1 = 2.0/9.0
      if (args.c2 is None):
        args.c2 = 0.8
      if (args.c3_i is None):  # INVERSE of new interface, also RES SEPCIFIC! 1.0 is for 1-degree!
        args.c3_i = 1.0
      if (args.c4 is None):
        args.c4 = 2.0
      if (args.c5 is None):
        args.c5 = 3.0
    elif args.model == 'psi':
      if (args.vslow is None):
        args.vslow = 250.0
      if (args.vfast is None):
        args.vfast = 650.0
      if (args.psi_eps is None):
        args.psi_eps = 0.05
      if (args.psi_width is None):
        args.psi_width = 0.025
    else:
      print('ERROR! Valid model options:  wsa, wsa2, psi')
      quit()

    rad_to_deg = 57.2957795130823

    ## Read data from input files
    xvec, yvec, data_dchb   = ps.rdhdf_2d(args.dchb)
    _,       _, data_expfac = ps.rdhdf_2d(args.expfac)

    NX = xvec.size
    NY = yvec.size

    v    = np.empty((NY, NX))
    rho  = np.empty((NY, NX))
    temp = np.empty((NY, NX))

    ## Compute the WSA solar wind speed
    if args.model == 'wsa':
      for i in range(NY):
        for j in range(NX):
            chd_value = data_dchb[i][j]
            chd_deg = chd_value * rad_to_deg
            chd_arg = args.c3_i * chd_deg
            chd_factor = 1.0 - args.c2 * np.exp(-chd_arg ** args.c4)
            ef_factor = (1.0 + data_expfac[i][j]) ** args.c1
            v[i][j] = args.vslow + (args.vfast / ef_factor) * chd_factor
            v[i][j] = min(v[i][j], args.vmax)

    ## Compute the WSA2 solar wind speed
    elif args.model == 'wsa2':
       for i in range(NY):
          for j in range(NX):
            chd_value = data_dchb[i][j]
            chd_deg = chd_value * rad_to_deg
            chd_arg = args.c3_i * chd_deg
            chd_factor = (1.0 - args.c2 * np.exp(-chd_arg ** args.c4)) ** args.c5
            ef_factor = (1.0 + data_expfac[i][j]) ** args.c1
            v[i][j] = args.vslow + (args.vfast / ef_factor) * chd_factor

    ## Compute the PSI ad hoc solar wind speed
    elif args.model == 'psi':
       for i in range(NY):
          for j in range(NX):
            chd_value = data_dchb[i][j]
            profile = 0.5 * (1.0 + np.tanh((chd_value - args.psi_eps) / args.psi_width))
            v[i][j] = args.vslow + (args.vfast - args.vslow) * profile

    # Compute the ad hoc density and temperature from
    # pressure balance, as is done in the original MAS_IP
    vmax = np.amax(v)
    for i in range(NY):
      for j in range(NX):
        rho[i][j] = args.rhofast * (vmax / v[i][j]) ** 2
        temp[i][j] = args.tfast * args.rhofast / rho[i][j]  

    ## Write data to output files:
    ps.wrhdf_2d('vr_r1.h5',  xvec, yvec, v)
    ps.wrhdf_2d('rho_r1.h5', xvec, yvec, rho)
    ps.wrhdf_2d('t_r1.h5',   xvec, yvec, temp)

if __name__ == '__main__':
    main()
