#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess
from pathlib import Path
import shutil
import re
import h5py as h5

import bin.psi_io as ps

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

  parser.add_argument('-rnum',
    help='Realization number to use for output file names (Default None).',
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

  parser.add_argument('-sw_model',
    help='Select solar wind model.',
    dest='sw_model',
    type=str,
    default='wsa2',
    required=False)

  parser.add_argument('-sw_model_params',
    help='Flags to pass to the solar wind model generation script eswim.py.\
          For WSA2:  -wsa2_vslow <#> -wsa2_vfast <#> -wsa2_c1 <#> -wsa2_c2 <#> -wsa2_c3_i <#> -wsa2_c4 <#> -wsa2_c5 <#>\
          For WSA1:  -wsa1_vslow <#> -wsa1_vfast <#> -wsa1_c1 <#> -wsa1_c2 <#> -wsa1_c3_i <#> -wsa1_c4 <#> -wsa1_vmax <#>\
          For DCHB:  -dchb_vslow <#> -dchb_vfast <#> -dchb_eps <#> -dchb_width <#>\
          For all models:  -rhofast <#> -tfast <#>',
    dest='sw_model_params',
    type=str,
    default='',
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
    
  parser.add_argument('-r0_trace',
    help='Set inner radius to trace field lines to/from (default is 1.0).',
    dest='r0_trace',
    type=float,
    default=1.0,
    required=False)

  parser.add_argument('-noplot',
    help='Do not plot results',
    dest='plot_results',
    action='store_false',
    default=True,
    required=False)
    
  parser.add_argument('-clearPF',
    help='Delete PFSS+CS 3D solutions after run.',
    dest='clearPF',
    action='store_true',
    default=False,
    required=False)    

  return parser.parse_args()

def run(args):
  # Get full path of input file:
  args.input_map = Path(args.input_map).resolve()

  # Make rundir and go there
  args.rundir = Path(args.rundir or f'{args.input_map.stem}_swig_run').resolve()

  # Add realization number folder if realization number provided
  if args.rnum:
    args.rundir /= f'r{args.rnum:06d}'

  # Make the run folder
  args.rundir.mkdir(parents=True, exist_ok=True)

  # Check if the hdf is 3D or 2D
  if is_3D_hdf(args.input_map):
    # If 3D extact realizations and process individually
    temp_dir = args.rundir / "temp_extract"
    print(temp_dir)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / args.input_map.name
    shutil.copy(args.input_map, temp_file)
    for file in extract_realization(temp_file):
      match = re.search(r'r(\d{6})', file)
      rundir = args.rundir / f'r{match.group(1)}' if match else args.rundir
      rundir.mkdir(exist_ok=True)
      process_map(args, file, rundir)

    shutil.rmtree(temp_dir)
  else:
    # Process 2D file
    match = re.search(r'r(\d{6})', str(args.input_map))
    if match:
      args.rnum = int(match.group(1))
    rundir = args.rundir / f'r{match.group(1)}' if match else args.rundir
    rundir.mkdir(exist_ok=True)
    process_map(args, str(args.input_map), rundir)

def process_map(args, input_map: str, rundir: Path):
  # Change to run directory
  os.chdir(rundir)
  # Get path of the SWiG directory
  swigdir = Path(sys.path[0])

  # Run PF model.
  print('=> Running PFSS+CS model with POT3D:')
  Command=f"{swigdir / 'bin' / 'cor_pfss_cs_pot3d.py'} {input_map} -np {args.np} -rss {args.rss} -r1 {args.r1}"
  run_command(Command)
  
  # Extract Br at tracing height:
  br_rtrace,x,y = ps.np_interpolate_slice_from_hdf(rundir / "pfss" / "br_pfss.h5",args.r0_trace,None,None,)
  ps.wrhdf_2d('br_rtrace.h5', x, y, br_rtrace)
  run_command(f"{swigdir / 'pot3d' / 'bin' / 'psi_plot2d'} -tp -cmin -25 -cmax 25 -ll -finegrid -unit_label Gauss br_rtrace.h5 -o br_rtrace.png -title 'Br at r={args.r0_trace}'")
  
  # Analyze and compute required quantities from model.
  print('=> Running magnetic tracing analysis:')

  Command=f"{swigdir / 'bin' / 'mag_trace_analysis.py'} -r0_trace {args.r0_trace} ."
  run_command(Command)
  run_command(f"{swigdir / 'pot3d' / 'bin' / 'psi_plot2d'} -tp -cmin -0.002 -cmax 0.002 -ll -finegrid -unit_label Gauss br_r1.h5 -o br_r1.png -cmap psi_blue_red -title 'Br at r={args.r1}'")

  # Calcualate solar wind(s):
  models = args.sw_model.split(',')
  for model_type in models:
  
    os.chdir(rundir)

    # Get proper list of params for the current model:
    model_type = model_type.strip()
    sw_model_params = filter_sw_model_params(args.sw_model_params, model_type)

    # Generate solar wind model.
    print(f'=> Calculating emperical solar wind for model {model_type} ...')
    Command=f"{swigdir / 'bin' / 'eswim.py'} -dchb dchb_at_r1.h5 -expfac expfac_rss_at_r1.h5 -model {model_type} {sw_model_params}"
    run_command(Command)

    # Collect results and plot everything if selected.
    print('=> Collecting results...')
    result_dir = collect_results(args, rundir, model_type)
    
    if args.plot_results:
      os.chdir(result_dir)
      plot_results(args, swigdir)
    
  if args.clearPF:
    print("=> Clearing 3D files in pfss and cs directories...")
    try:
      for file in (rundir / "pfss").glob("b[rtp]_pfss.h5"):
        file.unlink(missing_ok=True)
      for file in (rundir / "cs").glob("b[rtp]_cs.h5"):
        file.unlink(missing_ok=True)        
      for subdir in rundir.glob("r[0-9][0-9][0-9][0-9][0-9][0-9]"):
        if subdir.is_dir():
          for file in (subdir / "pfss").glob("b[rtp]_pfss.h5"):
            file.unlink(missing_ok=True)
          for file in (subdir / "cs").glob("b[rtp]_cs.h5"):
            file.unlink(missing_ok=True)      
    except Exception as e:
      print(f"Failed to remove files from {rundir}: {e}")

  print('=> SWiG complete!')
  print('=> Results can be found here:  ')
  print(f'   {rundir}/results')


def run_command(Command):
  print('   Command:  '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)

def collect_results(args, rundir, model):
  result_dir = rundir / 'results' / model
  result_dir.mkdir(parents=True,exist_ok=True)
  idxstr = f"_idx{args.oidx:06d}" if args.oidx is not None else ""
  files_to_move = ["vr_r1.h5", "t_r1.h5", "rho_r1.h5"]
  files_to_copy = {"br_r1.h5": "br_r1","pfss/ofm_r0.h5": "ofm_r0", "pfss/slogq_r0.h5": "slogq_r0", "pfss/br_r0_pfss.h5": "br_r0", "pfss/slogq_rss.h5": "slogq_rss"}
  for file in files_to_move:
    move_file(file, result_dir / f"{Path(file).stem}{idxstr}.h5")
  for src, dest in files_to_copy.items():
    copy_file(src, result_dir / f"{dest}{idxstr}.h5")
  return result_dir


def move_file(src, dest):
    ierr = os.system(f"mv {src} {dest}")
    check_error_code(ierr, f"Failed to move {src} to {dest}")


def copy_file(src, dest):
    ierr = os.system(f"cp {src} {dest}")
    check_error_code(ierr, f"Failed to copy {src} to {dest}")


def plot_results(args, swigdir):
    print("=> Plotting results...")
    idxstr = f"_idx{args.oidx:06d}" if args.oidx is not None else ""
    plots = [
        ('br_r0',     'Gauss',   -25,    25,      'finegrid', 'psi_blue_red'),
        ('slogq_r0',  '"slogQ"', -7,     7,       'finegrid', 'RdBu_r'),
        ('slogq_rss', '"slogQ"', -7,     7,       'finegrid', 'RdBu_r'),
        ('ofm_r0',    None,      -1,     1,       'finegrid', 'psi_blue_red'),
        ('t_r1',      'K',       200000, 2000000, 'finegrid', 'hot'),
        ('rho_r1',    '"#/cm^3"',  100,    800,     'finegrid', 'gnuplot2_r'),
        ('vr_r1',     'km/s',    200,    800,     'finegrid', 'rainbow'),
        ('br_r1',     'Gauss',   -0.002, 0.002,   'finegrid', 'psi_blue_red')
    ]

    for name, label, cmin, cmax, grid, cmap in plots:
      cmd = (f"{swigdir / 'pot3d' / 'bin' / 'psi_plot2d'} -tp {'-unit_label ' + label if label else ''} -cmin {cmin} -cmax {cmax} -ll -{grid} {name}{idxstr}.h5 {'-cmap ' + cmap if cmap else ''} -o {name}{idxstr}.png")
      ierr = os.system(cmd)
      check_error_code(ierr, f"Failed to plot {name}{idxstr}.h5")


def extract_realization(file):
  pvec, tvec, rvec, data = ps.rdhdf_3d(file)
  created_files = []
  for i in map(int, rvec):
    fname = f"{file.with_suffix('')}_r{i:06d}.h5"
    created_files.append(fname)
    ps.wrhdf_2d(fname, pvec, tvec, data[i - 1, :, :])
  return created_files


def is_3D_hdf(file):
  with h5.File(file, 'r') as h5file:
      ndims = np.ndim(h5file["Data"])
      if ndims == 3:
        return True
      elif ndims == 2:
        return False
      else:
        check_error_code(10,'Invalid number of dimensions ({ndims}) in {file_list[0]}') 


def check_error_code(ierr,message):
  if ierr > 0:
    print(' ')
    print(message)
    print('Error code of fail : '+str(ierr))
    sys.exit(1)
    
def filter_sw_model_params(sw_model_params, model_type):
  """
  Filter solar wind model parameters based on model type and remove appropriate prefixes.
  Args:
    sw_model_params: String of command-line flags from -sw_model_params
    model_type: String indicating model type ('wsa1', 'wsa2', or 'dchb')
  Returns:
    Filtered string with appropriate prefixes removed
  """
  if not sw_model_params:
    return ''
  tokens = sw_model_params.split()
  model_prefixes = {'wsa1': 'wsa1_', 'wsa2': 'wsa2_', 'dchb': 'dchb_'}
  common_flags = {'rhofast', 'tfast'}
  model_specific_flags = {
    'wsa1': {'vslow', 'vfast', 'c1', 'c2', 'c3_i', 'c4', 'vmax'},
    'wsa2': {'vslow', 'vfast', 'c1', 'c2', 'c3_i', 'c4', 'c5'},
    'dchb': {'vslow', 'vfast', 'eps', 'width'}
  }
  dchb_keep_prefix = {'eps', 'width'}  # dchb flags that keep the prefix
  if model_type not in model_prefixes:
    return ''
  prefix = model_prefixes[model_type]
  allowed_flags = model_specific_flags[model_type]
  filtered_tokens = []
  i = 0
  while i < len(tokens):
    token = tokens[i]
    if token.startswith('-'):
      flag_name = token[1:]
      # Keep common flags (rhofast, tfast)
      if flag_name in common_flags:
        filtered_tokens.append(token)
      # Keep prefix-less versions as-is
      elif flag_name in allowed_flags:
        filtered_tokens.append(token)
      # Check for model-specific flags with prefix
      elif flag_name.startswith(prefix):
        suffix = flag_name[len(prefix):]
        if model_type == 'dchb' and suffix in dchb_keep_prefix:
          # Keep prefix for dchb eps and width
          filtered_tokens.append(token)
        else:
          # Remove prefix for all wsa1/wsa2, and dchb vslow/vfast
          filtered_tokens.append('-' + suffix)
      else:
        i += 1
        continue
      # Add the value following the flag
      if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
        filtered_tokens.append(tokens[i + 1])
        i += 1
    i += 1
  return ' '.join(filtered_tokens)


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
# ### Version 1.2.0, 04/18/2024, modified by MS:
#       - Added realization support.
#
# ### Version 1.2.1, 05/14/2025, modified by RC:
#       - Fixed colormap for Q.
#
# ### Version 1.2.2, 06/18/2025, modified by RC:
#       - Updated for new pot3d submodule update.
#
# ### Version 1.3.0, 08/19/2025, modified by RC:
#       - Removed -gpu option as POT3D auto-detects this now.
#
# ### Version 1.4.0, 09/10/2025, modified by RC:
#       - Added -sw_model_params to pass solar wind parameters to 
#         solar wind generator script eswim.py.
#
# ### Version 1.5.0, 07/16/2025, modified by RC:
#       - Added clearPF flag to remove 3D PFSS+CS files to save disk space.
#
# ### Version 2.0.0, 07/22/2026, modified by RC:
#       - Changed name of PSI model to DCHB and WSA to WSA1.
#
# ### Version 2.1.0, 08.26.2026, modified by RC:
#       - Changed model param to allow multiple models to be computed 
#         in one SWiG run.  Note, the results are now in "results/model"
#         instead of "results".
#       - Some fixes to colormaps, unit labels, etc.
#
########################################################################
