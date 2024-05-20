#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess
from pathlib import Path

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
    help='Input Br full-Sun magnetogram (h5).',
    type=str)

  parser.add_argument('-oidx',
    help='Index to use for output file names).',
    required=False,
    type=int)

  parser.add_argument('-rundir',
    help='Directory where run will go.',
    dest='rundir',
    required=False,
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

  parser.add_argument('-noplot',
    help='Do not plot results',
    dest='plot_results',
    action='store_false',
    default=True,
    required=False)

  return parser.parse_args()

def run(args):

  # Get path of the SWiG directory:
  swigdir = sys.path[0]

  # Get full path of input file:
  args.input_map = str(Path(args.input_map).resolve())

  # Make rundir and go there
  if args.rundir is None:
      args.rundir = str(Path(args.input_map).stem)+'_swig_run'

  os.makedirs(args.rundir, exist_ok=True)

  os.chdir(args.rundir)

  # Run PF model.
  print('=> Running PFSS+CS model with POT3D:')
  Command=swigdir+'/bin/cor_pfss_cs_pot3d.py '+args.input_map+\
          ' -np '+str(args.np)+' -rss '+str(args.rss)+' -r1 '+str(args.r1)
  if (args.gpu):
    Command=Command+' -gpu'
  print('   Command:  '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)

  # Analyze and compute required quantities from model.
  print('=> Running magnetic tracing analysis:')
  Command=swigdir+'/bin/mag_trace_analysis.py .'
  print('   Command:  '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)

  # Generate solar wind model.
  print('=> Running emperical solar wind model:')
  Command=swigdir+'/bin/eswim.py -dchb dchb_at_r1.h5 '+\
          '-expfac expfac_rss_at_r1.h5 -model '+args.sw_model
  print('   Command:  '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)

  # Collect results and plot everything if selected.
  print('=> Collecting results...')
  result_dir = 'results'
  os.makedirs(result_dir, exist_ok=True)
  if args.oidx is not None:
    idxstr='_idx{:06d}'.format(args.oidx)
  else:
    idxstr=''
  ierr = os.system('mv br_r1.h5 '          + result_dir + '/br_r1'    + idxstr + '.h5')
  check_error_code(ierr,'Failed to move br_r1.h5 to '+ result_dir + '/br_r1'    + idxstr + '.h5')
  ierr = os.system('mv vr_r1.h5 '          + result_dir + '/vr_r1'    + idxstr + '.h5')
  check_error_code(ierr,'Failed to move vr_r1.h5 to '+ result_dir + '/vr_r1'    + idxstr + '.h5')
  ierr = os.system('mv t_r1.h5 '           + result_dir + '/t_r1'     + idxstr + '.h5')
  check_error_code(ierr,'Failed to move t_r1.h5 to '+ result_dir + '/t_r1'    + idxstr + '.h5')
  ierr = os.system('mv rho_r1.h5 '         + result_dir + '/rho_r1'   + idxstr + '.h5')
  check_error_code(ierr,'Failed to move rho_r1.h5 to '+ result_dir + '/rho_r1'    + idxstr + '.h5')
  ierr = os.system('cp pfss/ofm_r0.h5 '    + result_dir + '/ofm_r0'   + idxstr + '.h5')
  check_error_code(ierr,'Failed to copy pfss/ofm_r0.h5 to '+ result_dir + '/ofm_r0'   + idxstr + '.h5')
  ierr = os.system('cp pfss/slogq_r0.h5 '  + result_dir + '/slogq_r0' + idxstr + '.h5')
  check_error_code(ierr,'Failed to copy pfss/slogq_r0.h5 to '+ result_dir + '/slogq_r0'   + idxstr + '.h5')
  ierr = os.system('cp pfss/br_r0_pfss.h5 '+ result_dir + '/br_r0'    + idxstr + '.h5')
  check_error_code(ierr,'Failed to copy pfss/br_r0_pfss.h5 to '+ result_dir + '/br_r0'   + idxstr + '.h5')
  ierr = os.system('cp pfss/slogq_rss.h5 '  + result_dir + '/slogq_rss' + idxstr + '.h5')
  check_error_code(ierr,'Failed to copy pfss/slogq_rss.h5 to '+ result_dir + '/slogq_rss'   + idxstr + '.h5')

  os.chdir(result_dir)
  if args.plot_results:
    print('=> Plotting results...')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label Gauss     -cmin -20    -cmax 20      -ll -finegrid    br_r0'+idxstr+'.h5                  -o    br_r0'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot br_r0'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label "slog(Q)" -cmin -7     -cmax 7       -ll -finegrid slogq_r0'+idxstr+'.h5 -cmap RdBu       -o slogq_r0'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot slogq_r0'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label "slog(Q)" -cmin -7     -cmax 7       -ll -finegrid slogq_rss'+idxstr+'.h5 -cmap RdBu       -o slogq_rss'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot slogq_rss'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp                       -cmin -1     -cmax 1       -ll -finegrid   ofm_r0'+idxstr+'.h5                  -o   ofm_r0'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot ofm_r0'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label K         -cmin 200000 -cmax 2000000 -ll -finegrid     t_r1'+idxstr+'.h5 -cmap hot        -o     t_r1'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot t_r1'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label g/cm^3    -cmin 100    -cmax 800     -ll -finegrid   rho_r1'+idxstr+'.h5 -cmap gnuplot2_r -o   rho_r1'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot rho_r1'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label km/s      -cmin 200    -cmax 700     -ll -finegrid    vr_r1'+idxstr+'.h5 -cmap jet        -o    vr_r1'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot vr_r1'+idxstr+'.h5')
    ierr = os.system(swigdir+'/pot3d/scripts/psi_plot2d -tp -unit_label Gauss     -cmin -0.002 -cmax 0.002   -ll -finegrid    br_r1'+idxstr+'.h5                  -o    br_r1'+idxstr+'.png')
    check_error_code(ierr,'Failed to plot br_r1'+idxstr+'.h5')

  print('=> SWiG complete!')
  print('=> Results can be found here:  ')
  print('   '+str(Path('../'+result_dir).resolve()))
 

def check_error_code(ierr,message):
  if ierr > 0:
    print(' ')
    print(message)
    print('Error code of fail : '+str(ierr))
    sys.exit(1)


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

