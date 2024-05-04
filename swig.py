#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess

########################################################################
# SWiG:  Solar Wind Generator
#        Generate solar wind quantities using PFSS+CS magnetic fields
#        combined with emperical solar wind models.
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
  parser = argparse.ArgumentParser(description='Generate solar wind quantities using PFSS+CS magnetic fields combined with emperical solar wind models.')

  parser.add_argument('input_map',
    help='Input Br full-Sun magnetogram.',
    type=str)

  parser.add_argument('rundir',
    help='Directory where run will go.',
    type=str)

  parser.add_argument('-np',
    help='Number of MPI processes (ranks)',
    dest='np',
    type=int,
    default=1,
    required=False)

  parser.add_argument('-gpu',
    help='Indicate that POT3D will be run on GPUs.',
    dest='gpu',
    action='store_true',
    default=False,
    required=False)

  parser.add_argument('-sw_model',
    help='Select solar wind model.',
    dest='sw_model',
    type=str,
    default='wsa2',
    required=False)

  parser.add_argument('-rss',
    help='Set source surface radius (default 2.5 Rs).',
    dest='rss',
    type=float,
    default=2.5,
    required=False)

  parser.add_argument('-r1',
    help='Set outer radius (default 21.5 Rs).',
    dest='r1',
    type=float,
    default=21.5,
    required=False)

  parser.add_argument('-plot',
    help='Plot results',
    dest='plot_results',
    action='store_true',
    default=False,
    required=False)

  return parser.parse_args()

def run(args):

  # Get path of the SWiG directory:
  swigdir = sys.path[0]

  # Make rundir and go there
  os.makedirs(args.rundir, exist_ok=True)
  os.chdir(args.rundir)

  # Run PF model.
  Command=swigdir+'/bin/cor_pfss_cs_pot3d.py '+args.input_map+\
          ' -np '+str(args.np)+' -rss '+str(args.rss)+' -r1 '+str(args.r1)
  if (args.gpu):
    Command=Command+' -gpu'
  print('=> Running command:  '+Command)
  subprocess.run(["bash","-c",Command])

  # Analyze and compute required quantities from model.
  Command=swigdir+'/bin/mag_trace_analysis.py '+args.rundir
  print('=> Running command:  '+Command)
  subprocess.run(["bash","-c",Command])

  # Generate solar wind model.
  Command=swigdir+'/bin/eswim.py -dchb '+args.rundir+'/dchb_at_r1.h5 '+\
          '-expfac '+args.rundir+'/expfac_rss_at_r1.h5 -model '+args.sw_model
  print('=> Running command:  '+Command)
  subprocess.run(["bash","-c",Command])

  # Collect results and plot everything if selected.
  os.makedirs(args.rundir+'/results', exist_ok=True)
  os.chdir(args.rundir+'/results')


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
# ### Version 1.1.0, 04/18/2024, modified by RC:
#       - Initial working version.
#
########################################################################

