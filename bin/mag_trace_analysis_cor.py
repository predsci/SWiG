#!/usr/bin/env python3
import os
import sys
import subprocess
import numpy as np
import argparse
import psi_io as ps

########################################################################
#  MAG_TRACE_ANALYSIS_COR #
########################################################################
#
# INPUT:   Directory of run (where 3D coronal magnetic field data resides)
# OUTPUT:  expfac_rss_at_r1.h5, dchb_at_r1.h5
#          ofm_r0.h5, slogq_r0.h5
#
########################################################################
#          Predictive Science Inc.
#          www.predsci.com
#          San Diego, California, USA 92121
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
  parser = argparse.ArgumentParser(description='Get magnetic field tracing analysis quantities given a MAS MHD coronal solution.')

  parser.add_argument('rundir',
    help='Directory of run (where MHD was computed)',
    type=str)

  parser.add_argument('brfile',help='Name of Br file',type=str)
  parser.add_argument('btfile',help='Name of Bt file',type=str)
  parser.add_argument('bpfile',help='Name of Bp file',type=str)

  parser.add_argument('-r0_trace',
    help='Set inner radius to trace field lines to/from (default is rmin of PFSS).',
    dest='r0_trace',
    type=float,
    default=1.0,
    required=False)

  parser.add_argument('-r1',
    help='Outer radius to compute Q, expansion factor, and DCHB (Default is outer boundary of B field)',
    required=False,
    type=float,
    default=0)

  parser.add_argument('-uniform',
    help='Set uniform resolution for tracing points in theta and phi.  The default is twice the solution resolution, \
      otherwise one can use the -nt and -np to specify the tracing resolution.  \
      If not set, the tracing points will mimic the original non-uniform grid but at twice the resolution minus one.',
    required=False,
    action='store_true')

  parser.add_argument('-nt',
    help='Number of uniform theta points to trace with.',
    required=False,
    type=int)

  parser.add_argument('-np',
    help='Number of uniform phi points to trace with.',
    required=False,
    type=int)

  parser.add_argument('-mesh_t',
    help='Location of custom t mesh to use (full path)',
    required=False,
    type=str)

  parser.add_argument('-mesh_p',
    help='Location of custom p mesh to use (full path)',
    required=False,
    type=str)

  return parser.parse_args()

def get_sed_command():
  """Detect which sed command to use and return appropriate arguments.
  
  Returns: (sed_cmd, suffix_args) where suffix_args is [''] for BSD sed or [] for GNU sed
  """
  # First check if gsed (GNU sed) is available
  result = subprocess.run(['which', 'gsed'], capture_output=True, text=True)
  if result.returncode == 0:
    return ('gsed', [])
  
  # Check if system sed is GNU sed by testing --version flag
  result = subprocess.run(['sed', '--version'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  if result.returncode == 0:
    # GNU sed supports --version
    return ('sed', [])
  else:
    # BSD sed (macOS) doesn't support --version and requires '' after -i
    return ('sed', [''])

# Cache the sed command detection
_sed_cmd, _sed_suffix = get_sed_command()

def sed(match,value,file):
  match_pattern = '.*' + match + '=.*'
  replace_pattern = '  ' + match + '=' + value
  sed_directive = f's@{match_pattern}@{replace_pattern}@'
  cmd = [_sed_cmd, '-i'] + _sed_suffix + [sed_directive, file]
  ierr = subprocess.run(cmd).returncode
  check_error_code(ierr, 'Failed on sed of '+match+' in '+file)

def run(args):

  print('===========================================')
  print('===========================================')
  print('=> Starting Magnetic field trace analysis')
  print('===========================================')
  print('===========================================')

  # Get path of the rsrc directory where the template
  # MAPFL input files reside.
  # Here, assume this script is in the "bin" folder of SWiG.
  bindir = sys.path[0]
  rsrcdir = bindir+'/../rsrc/'
  rundir = os.path.abspath(args.rundir)
  psi_plot2d_loc = bindir+'/../pot3d/bin/psi_plot2d'

  # Get filenames of template input files.
  mapfl_file = rsrcdir+'/mapfl_cor.in'
  print('=> MAPFL input template used for MAS: '+mapfl_file)

  mapfl=bindir+'/../mapfl/bin/mapfl'

  # Change directory to the run directory.
  os.chdir(args.rundir)

  # Setup the COR MAPFL tracing:
  print("=> Running MAPFL on coronal solution... ")

  os.makedirs("mag_trace_analysis", exist_ok=True)

  os.chdir("mag_trace_analysis")

  ierr = subprocess.run(['cp', mapfl_file, 'mapfl.in']).returncode
  check_error_code(ierr,'Failed on copy of '+mapfl_file+' to mapfl.in')

  sed("bfile%r","'"+rundir+'/'+args.brfile+"'",'mapfl.in')
  sed("bfile%t","'"+rundir+'/'+args.btfile+"'",'mapfl.in')
  sed("bfile%p","'"+rundir+'/'+args.bpfile+"'",'mapfl.in')
  sed("r1 = ",str(args.r1),'mapfl.in')

  if not (args.mesh_t or args.mesh_p):
    _, tvec, pvec, _ = ps.rdhdf_3d(rundir+'/'+args.brfile)

  if args.mesh_t:
    sed("mesh_file_t",args.mesh_t,'mapfl.in')
  else:
    if args.uniform:
      sed("mesh_file_t","' '",'mapfl.in')
      if args.nt is None:
        sed("ntss",str(len(tvec)*2),'mapfl.in')
      else:
        sed("ntss",str(args.nt),'mapfl.in')
    else:
      tvec_new = add_midpoints(tvec)
      ps.wrhdf_1d('mesh_file_t_resX2.h5', tvec_new, tvec_new)
      sed("mesh_file_t","'mesh_file_t_resX2.h5'",'mapfl.in')

  if args.mesh_p:
    sed("mesh_file_p=",args.mesh_p,'mapfl.in')
  else:
    if args.uniform:
      sed("mesh_file_p","' '",'mapfl.in')
      if args.np is None:
        sed("npss",str(len(pvec)*2),'mapfl.in')
      else:
        sed("npss",str(args.np),'mapfl.in')
    else:
      pvec_new = add_midpoints(pvec)
      ps.wrhdf_1d('mesh_file_p_resX2.h5', pvec_new, pvec_new)
      sed("mesh_file_p","'mesh_file_p_resX2.h5'",'mapfl.in')

  # Set the lower tracing limits and dimensions:
  sed('ch_map_r',str(args.r0_trace),'mapfl.in')
  sed('domain_r_min',str(args.r0_trace),'mapfl.in')

  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  line_to_check='A field line did not reach'
  check_file_for_line(line_to_check,'mapfl.log','Failed : A field line did not reach R0 or R1.')

  print("=> Calculating the distance to open field boundaries (DCHB)... ")
  dchb_command = 'ch_distance.py -t r1_r0_t.h5 -p r1_r0_p.h5 -force_ch -chfile ofm_r0.h5 -dfile dchb_r1.h5'
  ierr = os.system(dchb_command)
  check_error_code(ierr,'Failed on : ' + dchb_command)

  print('=> Plotting results...')

  ierr = os.system(psi_plot2d_loc+' -tp -unit_label "slog(Q)" -cmin -7 -cmax 7 -ll -finegrid slogq_r0.h5 -cmap RdBu -o slogq_r0.png')
  check_error_code(ierr,'Failed to plot slogq_r0.h5')

  ierr = os.system(psi_plot2d_loc+' -tp -unit_label "slog(Q)" -cmin -7 -cmax 7 -ll -finegrid slogq_r1.h5 -cmap RdBu -o slogq_r1.png')
  check_error_code(ierr,'Failed to plot slogq_r1.h5')

  ierr = os.system(psi_plot2d_loc+' -tp -cmin -1 -cmax 1 -ll -finegrid ofm_r0.h5 -o ofm_r0.png')
  check_error_code(ierr,'Failed to plot ofm_r0.h5')

  ierr = os.system(psi_plot2d_loc+' -tp -cmin 0 -ll -finegrid dchb_r1.h5 -cmap RdBu         -o dchb_r1.png')
  check_error_code(ierr,'Failed to plot dchb_r1.h5')

  ierr = os.system(psi_plot2d_loc+' -tp -cmin 0 -cmax 500 -ll -finegrid expfac_r1_r0.h5   -cmap jet -o expfac_r1_r0.png')
  check_error_code(ierr,'Failed to plot expfac_r1_r0.h5')

  print("    ...done!")

def check_error_code(ierr,message):
  if ierr > 0:
    print(' ')
    print(message)
    print('Error code of fail : '+str(ierr))
    sys.exit(1)

def check_file_for_line(line_to_check,file,message):
  Command='grep "'+line_to_check+'" '+file
  ierr = subprocess.run(["bash","-c",Command],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  ierr = 1 if ierr.returncode == 0 else 0
  check_error_code(ierr,message)

def add_midpoints(grid):
    midpoints = (grid[:-1] + grid[1:]) / 2.0
    new_grid = np.empty(len(grid) + len(midpoints))
    new_grid[0::2] = grid
    new_grid[1::2] = midpoints
    return new_grid

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
# ### Version 1.0.1, 09/03/2025, modified by RC:
#       - Fixed sed bug.
#
# ### Version 1.1.0, 11/05/2025, modified by MS:
#       - Changed sed command so it can also work on macOS.
#
########################################################################
