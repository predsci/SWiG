#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from pathlib import Path
import re

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

  # Get full path of input directory:
  input_directory = Path(args.input_directory).resolve()

  # Set default output directory if needed.
  if args.outdir is None:
      args.outdir = str(Path('.').resolve())+'/output_swig'

  # Get all files in input directory
  h5_files = list(input_directory.glob('*.h5'))

  if len(h5_files) < 1:
    print(' ')
    print('No h5 files found.')
    sys.exit(1)

  if args.swig_path is None:
    pmpdir = sys.path[0]
    args.swig_path = pmpdir+'/../swig.py'

  args.swig_path = str(Path(args.swig_path).resolve())

  empty_idx=99999
  for h5_file in h5_files:
    h5_file=str(h5_file)
    idx=h5_file[-9:-3]
    if bool(re.search(r'\d{6}',idx)):
      oidx=' -oidx '+idx
    else:
      oidx=' -oidx '+str(empty_idx)
      empty_idx+=1

    print('=> Running map : ' +h5_file.split('/')[-1])
    Command=args.swig_path+' '+h5_file+' -rundir '+args.outdir+oidx+ \
      ' -np '+str(args.np)+' -sw_model '+args.sw_model+\
      ' -rss '+str(args.rss)+' -r1 '+str(args.r1)
    if (args.gpu):
      Command=Command+' -gpu'
    if (not args.plot_results):
      Command=Command+' -noplot'
    ierr = subprocess.run(["bash","-c",Command])
    check_error_code_NON_CRASH(ierr.returncode,'Failed : '+Command)

    print('=> Clearing pfss and cs directory')
    ierr = os.system('rm '+args.outdir+'/pfss/*')
    check_error_code(ierr,'Failed to remove files from '+args.outdir+'/pfss/')
    ierr = os.system('rm '+args.outdir+'/cs/*')
    check_error_code(ierr,'Failed to remove files from '+args.outdir+'/cs/')


def check_error_code_NON_CRASH(ierr,message):
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
