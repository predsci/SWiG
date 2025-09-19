#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from pathlib import Path
import re
import h5py as h5
import numpy as np
import psi_io as ps
import shutil

# INPUT:  - Map directory (use Path from pathlib to get full path)
#         - Output directory (default is new local folder called "output_swig")
#         - [Need rest of swig options to pass to the swig call]

def argParsing():
  parser = argparse.ArgumentParser(description='Run multiple maps through SWiG.')

  parser.add_argument('input_directory',
    help='Input directory of Br full-Sun magnetograms (h5).',
    type=str)

  parser.add_argument('-outdir',
    help='Directory where output will go.',
    dest='outdir',
    required=False,
    type=str)

  parser.add_argument('-swig_path',
    help='Path to swig.py.',
    dest='swig_path',
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
          For WSA2:  -vslow <#> -vfast <#> -c1 <#> -c2 <#> -c3_i <#> -c4 <#> -c5 <#>\
          For WSA:   -vslow <#> -vfast <#> -c1 <#> -c2 <#> -c3_i <#> -c4 <#> -vmax <#>\
          For PSI:   -vslow <#> -vfast <#> -psi_eps <#> -psi_width <#>\
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

  return parser.parse_args()

def run(args):

  # Get full path of input directory:
  input_directory = Path(args.input_directory).resolve()
  
  # Set default output directory if needed.
  args.outdir = Path(args.outdir or "./output_swig").resolve()

  # Get all files in input directory
  h5_files = sorted(input_directory.glob("*.h5"))

  if not h5_files:
    print("\nNo h5 files found.")
    sys.exit(1)

  args.swig_path = Path(args.swig_path or f"{sys.path[0]}/../swig.py").resolve()

  for h5_file in h5_files:
    if is_3D_hdf(h5_file):
      rvec = extract_realization(h5_file)
      process_file(args, h5_file, rvec)
    else:
      process_file(args, h5_file, None)


def process_file(args, h5_file, rvec):
  idx_match = re.search(r"idx(\d{6})", str(h5_file))
  idx = idx_match.group(1) if idx_match else "999999"

  print(f"=> Running map: {h5_file.name}")

  r0_trace_str = f"-r0_trace {arg.r0_trace}"
  
  command = (
    f"{args.swig_path} {h5_file} -rundir {args.outdir} -oidx {idx} "
    f"-np {args.np} -sw_model {args.sw_model} {r0_trace_str}"
    f"-sw_model_params {args.sw_model_params} -rss {args.rss} -r1 {args.r1} ")

  if not args.plot_results:
    command += "-noplot "

  ierr = subprocess.run(["bash", "-c", command])
  check_error_code_non_crash(ierr.returncode, f"Failed: {command}")

  print("=> Clearing pfss and cs directories")
  remove_files(args.outdir, rvec)


def remove_files(output_dir, rvec):
  if rvec is not None:
    for r in rvec:
      clear_directory(output_dir / f"r{int(r):06d}/pfss")
      clear_directory(output_dir / f"r{int(r):06d}/cs")
  else:
    clear_directory(output_dir / "pfss")
    clear_directory(output_dir / "cs")


def clear_directory(directory):
  try:
    shutil.rmtree(directory, ignore_errors=True)
  except Exception as e:
    print(f"Failed to remove files from {directory}: {e}")


def extract_realization(file):
  _, _, rvec, _ = ps.rdhdf_3d(file)
  return np.array(rvec)


def is_3D_hdf(file):
  with h5.File(file, 'r') as h5file:
    ndims = np.ndim(h5file["Data"])
    if ndims == 3:
      return True
    elif ndims == 2:
      return False
    else:
      check_error_code(10,'Invalid number of dimensions ({ndims}) in {file_list[0]}') 


def check_error_code_non_crash(ierr,message):
  if ierr > 0:
    print(' ')
    print(message)
    print('Error code of fail : '+str(ierr))


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

# ### Version 1.1.0, 08/19/2025, modified by RC:
#       - Removed -gpu option as POT3D auto-detects this now.
# ### Version 2.0.0, 09/18/2025, modified by RC:
#      - Added new swig options.
