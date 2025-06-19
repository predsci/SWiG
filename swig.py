#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess
from pathlib import Path
import h5py as h5
import bin.psi_io as ps
import shutil
import re

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
  if (args.gpu):
    Command=f"{Command} -gpu"
  run_command(Command)
  
  # Analyze and compute required quantities from model.
  print('=> Running magnetic tracing analysis:')
  Command=f"{swigdir / 'bin' / 'mag_trace_analysis.py'} ."
  run_command(Command)

  # Generate solar wind model.
  print('=> Running emperical solar wind model:')
  Command=f"{swigdir / 'bin' / 'eswim.py'} -dchb dchb_at_r1.h5 -expfac expfac_rss_at_r1.h5 -model {args.sw_model}"
  run_command(Command)

  # Collect results and plot everything if selected.
  print('=> Collecting results...')
  result_dir = collect_results(args, rundir)
    
  if args.plot_results:
    plot_results(args, swigdir, result_dir)
    
    print(f"=> SWiG complete!\n=> Results can be found here: {rundir / 'results'}")

  print('=> SWiG complete!')
  print('=> Results can be found here:  ')
  print(f'   {result_dir}')


def run_command(Command):
  print('   Command:  '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)

def collect_results(args, rundir):
  result_dir = rundir / 'results'
  result_dir.mkdir(exist_ok=True)
  idxstr = f"_idx{args.oidx:06d}" if args.oidx is not None else ""
  files_to_move = ["br_r1.h5", "vr_r1.h5", "t_r1.h5", "rho_r1.h5"]
  files_to_copy = {"pfss/ofm_r0.h5": "ofm_r0", "pfss/slogq_r0.h5": "slogq_r0", "pfss/br_r0_pfss.h5": "br_r0", "pfss/slogq_rss.h5": "slogq_rss"}
    
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


def plot_results(args, swigdir, result_dir):
    os.chdir(result_dir)
    print("=> Plotting results...")
    idxstr = f"_idx{args.oidx:06d}" if args.oidx is not None else ""
    plots = [
        ('br_r0',     'Gauss',   -20,    20,      'finegrid', None),
        ('slogq_r0',  '"slog(Q)"', -7,     7,       'finegrid', 'RdBu_r'),
        ('slogq_rss', '"slog(Q)"', -7,     7,       'finegrid', 'RdBu_r'),
        ('ofm_r0',    None,      -1,     1,       'finegrid', None),
        ('t_r1',      'K',       200000, 2000000, 'finegrid', 'hot'),
        ('rho_r1',    'g/cm^3',  100,    800,     'finegrid', 'gnuplot2_r'),
        ('vr_r1',     'km/s',    200,    700,     'finegrid', 'jet'),
        ('br_r1',     'Gauss',   -0.002, 0.002,   'finegrid', None)
    ]
    
    for name, label, cmin, cmax, grid, cmap in plots:
      cmd = (f"{swigdir / 'pot3d' / 'scripts' / 'psi_plot2d'} -tp {'-unit_label ' + label if label else ''} -cmin {cmin} -cmax {cmax} -ll -{grid} {name}{idxstr}.h5 {'-cmap ' + cmap if cmap else ''} -o {name}{idxstr}.png")
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
########################################################################
