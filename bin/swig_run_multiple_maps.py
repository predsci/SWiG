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

  parser.add_argument('-keep3D',
    help='Do not delere PFSS+CS 3D solutions',
    dest='keep3d',
    action='store_true',
    default=False,
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
  
    print(f"=> Running map: {h5_file.name}")
  
    basename = h5_file.stem
    
    if len(basename) >= 6 and basename[-6:].isdigit():
      idx = basename[-6:]
    else:
      idx_match = re.search(r"idx(\d{6})", basename)
      idx = idx_match.group(1) if idx_match else "999999"
    
    #Make directory based on map name and go into it:
    original_cwd = Path.cwd()
    rundir = Path(basename)

    command = (
      f"{args.swig_path} {h5_file} -rundir {rundir} -oidx {idx} "
      f"-np {args.np} -r0_trace {args.r0_trace} "
      f"-rss {args.rss} -r1 {args.r1} ")

    if not args.plot_results:
      command += "-noplot "
      
    if args.sw_model_params and args.sw_model_params != "":
      command += f" -sw_model_params {args.sw_model_params}"
      
    if not args.keep3d:
     command += f" -clearPF "
      
    ierr = subprocess.run(["bash", "-c", command])
    check_error_code_non_crash(ierr.returncode, f"Failed: {command}")
       
    os.chdir(original_cwd)        


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
#
# ### Version 2.0.0, 09/18/2025, modified by RC:
#      - Added new swig options.
#
# ### Version 3.0.0, 07/16/2026, modified by RC:
#      - Simplified script and now each map is in its own folder.
#        Maps no longer have idx label.
#