#!/usr/bin/env python3
import numpy as np
import argparse
#
import psih5 as ps

# E-SWiM:  Empirical Solar Wind Models
#
# Authors:
#           Savir Basil
#           Ronald M. Caplan
#           Jon A. Linker
#
# Version 1.0.1
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

    ## INXut file names
    parser.add_argument("-dchb",   type=str, 
                        help='Distance to coronal hole boundaries (DCHB) hdf5 filename.', required=True)
    parser.add_argument("-expfac", type=str, 
                        help='Expansion factor hdf5 filename.', required=True)

    ## Model type selected
    parser.add_argument("-model",type=str,help='Model type. Allowed model types are: wsa, wsa2, psi', required=True)

    ## Parameters for the WSA model
    parser.add_argument("-wsa_vslow", type=float, required=False,
                        help='Slow wind speed [km/s]')
    parser.add_argument("-wsa_vfast", type=float, required=False,
                        help='Fast wind speed [km/s]')
    parser.add_argument("-wsa_vmax", type=float, required=False,
                        help='Maximum wind speed [km/s]')
    parser.add_argument("-wsa_ef_power", type=float, required=False,
                        help='Expansion factor power')
    parser.add_argument("-wsa_chd_mult_fac", type=float, required=False,
                        help='CH distance multiplier')
    parser.add_argument("-wsa_chd_arg_fac", type=float, required=False,
                        help='CH distance factor')
    parser.add_argument("-wsa_chd_power", type=float, required=False,
                        help='CH distance power')
    parser.add_argument("-wsa_c5", type=float, required=False,
                        help='C5')

    ## Parameters for the PSI empirical solar wind speed model
    parser.add_argument("-psi_vslow", type=float, required=False,
                        help='Slow wind speed [km/s]')
    parser.add_argument("-psi_vfast", type=float, required=False,
                        help='Fast wind speed [km/s]')
    parser.add_argument("-psi_eps", type=float, required=False,
                        help='CH distance parameter')
    parser.add_argument("-psi_width", type=float, required=False,
                        help='CH distance width')

    ## Parameters for the density and temperature
    parser.add_argument("-rhofast", type=float, default=152.0, required=False,
                        help='Fast wind density  [#/cm3]')
    parser.add_argument("-tfast", type=float, default=1.85e6, required=False,
                        help='Fast wind temperature [K]')

    return parser.parse_args()

def main():

    ## Get iinput arguments:
    args = argParsing()

    ## Set defaults based on model:
    if args.model == 'wsa':
      if (args.wsa_vslow is None):
        args.wsa_vslow = 250.0
      if (args.wsa_vfast is None):
        args.wsa_vfast = 680.0
      if (args.wsa_vmax is None):
        args.wsa_vmax = 800.0
      if (args.wsa_ef_power is None):
        args.wsa_ef_power = 1.0/3.0
      if (args.wsa_chd_mult_fac is None):
        args.wsa_chd_mult_fac = 0.8
      if (args.wsa_chd_arg_fac is None):
        args.wsa_chd_arg_fac = 0.25
      if (args.wsa_chd_power is None):
        args.wsa_chd_power = 4.0
    elif args.model == 'wsa2':
      if (args.wsa_vslow is None):
        args.wsa_vslow = 285.0
      if (args.wsa_vfast is None):
        args.wsa_vfast = 625.0
      if (args.wsa_ef_power is None):
        args.wsa_ef_power = 2.0/9.0
      if (args.wsa_chd_mult_fac is None):
        args.wsa_chd_mult_fac = 0.8
      if (args.wsa_chd_arg_fac is None):
        args.wsa_chd_arg_fac = 0.5
      if (args.wsa_chd_power is None):
        args.wsa_chd_power = 2.0
      if (args.wsa_c5 is None):
        args.wsa_c5 = 3.0
    elif args.model == 'psi':
      if (args.psivslow is None):
        args.psi_vslow = 250.0
      if (args.psi_vfast is None):
        args.psi_vfast = 650.0
      if (args.psi_eps is None):
        args.psi_eps = 0.050
      if (args.psi_width is None):
        args.psi_width = 0.025
    else:
      print('ERROR!  Only wsa, wsa2, and psi models allowed.')
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
            chd_arg = args.wsa_chd_arg_fac * chd_deg
            chd_factor = 1.0 - args.wsa_chd_mult_fac * np.exp(-chd_arg ** args.wsa_chd_power)
            ef_factor = (1.0 + data_expfac[i][j]) ** args.wsa_ef_power
            v[i][j] = args.wsa_vslow + (args.wsa_vfast / ef_factor) * chd_factor
            v[i][j] = min(v[i][j], args.wsa_vmax)

    ## Compute the WSA2 solar wind speed
    elif args.model == 'wsa2':
       for i in range(NY):
          for j in range(NX):
            chd_value = data_dchb[i][j]
            chd_deg = chd_value * rad_to_deg
            chd_arg = args.wsa_chd_arg_fac * chd_deg
            chd_factor = (1.0 - args.wsa_chd_mult_fac * np.exp(-chd_arg ** args.wsa_chd_power)) ** args.wsa_c5
            ef_factor = (1.0 + data_expfac[i][j]) ** args.wsa_ef_power
            v[i][j] = args.wsa_vslow + (args.wsa_vfast / ef_factor) * chd_factor

    ## Compute the PSI ad hoc solar wind speed
    elif args.model == 'psi':
       for i in range(NY):
          for j in range(NX):
            chd_value = data_dchb[i][j]
            profile = 0.5 * (1.0 + np.tanh((chd_value - args.psi_eps) / args.psi_width))
            v[i][j] = args.psi_vslow + (args.psi_vfast - args.psi_vslow) * profile

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
