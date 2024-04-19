#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse

##############################
# SWiG:  Solar Wind Generator
#        Generate solar wind quantities using PFSS+CS magnetic fields combined
#        with emperical solar wind models.
#############################

def argParsing():
  parser = argparse.ArgumentParser(description='Generate solar wind quantities using PFSS+CS magnetic fields combined with emperical solar wind models.')

  parser.add_argument('rundir',
    help='Directory where run will go.',
    dest='rundir',
    type=str)

  parser.add_argument('input_map',
    help='Input Br full-Sun magnetogram.',
    dest='br_input_file',
    type=str)

  parser.add_argument('-np',
    help='Number of MPI processes (ranks)',
    dest='np',
    type=int,
    default=1,
    required=False)

  parser.add_argument('-sw_model',
    help='Select solar wind model.',
    dest='sw_model',
    type=str,
    default='wsa2',
    required=False)

  parser.add_argument('-gpu',
    help='Indicate that POT3D will be run on GPUs.',
    dest='gpu',
    action='store_true',
    default=False,
    required=False)

  return parser.parse_args()

def run(args):

  # Get path of the SWiG directory

  swigdir = sys.path[0]

  # Make rundir and go there
  os.makedirs(args.rundir, exist_ok=True)
  os.chdir(args.rundir)

  # Run PF model.

  os.system(swigdir+'/bin/cor_pfss_cs_pot3d.py '+args.br_input_file+' -np '+args.np)

  # Analyze and compute required quantities from model.

  os.system(swigdir+'/bin/mag_trace_analysis.py '+args.rundir)

  # Make results folder.
  os.makedirs(args.rundir+'/results', exist_ok=True)
  os.chdir(args.rundir+'/results')

  # Generate solar wind model.

  os.system(swigdir+'/bin/eswim.py -dchb '+args.rundir+'/dchb_r1.h5'+\
             '-expfac '+args.rundir+'/expfac_r1_r0.h5 -model '+args.sw_model)

  # Copy other results and plot everything.

  #  .....


def main():
  args = argParsing()
  run(args)

if __name__ == '__main__':
  main()

########################################################################
#
# ### CHANGELOG
#
# ### Version 1.0.0, 04/18/2024, modified by RC:
#       - Initial versioned version.
#
########################################################################








# FORTRAN TOOLS NEEDED:
# 1) POT3D         [github]
# 2) MAPFL         [github]
# 3) SLICE         [?  Maybe convert to py?]

#Output: verbose level is V#
# V0  2D Solar wind and field at r1 (rho, vr, temp, br)
# V0  2D Br at Rss and R0
# V0  2D Open Field (CH) map at r0
# V0  Meta data file with actual rss, r1, etc. values
# V1  3D PFSS and CS fields (CS field with polarity)
# V2  2D Expansion factors and distance to OF boundaries at r0, rss, and r1

# Input: Required vs Optional
#   rss : (default 2.5) rss radius (default r resolutions based on 2.5...)
#   r1  : (default 21.5) outer radius for solar wind data calucaltion and outer radius of CS model



