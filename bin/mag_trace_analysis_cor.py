#!/usr/bin/env python3
import os
import sys
import subprocess
import numpy as np
import argparse

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
  parser = argparse.ArgumentParser(description='Generate.')

  parser.add_argument('rundir',
    help='Directory of run',
    type=str)   
    
    # Br, Bt, and Bp files
    # R1 (optional)
    # res_t, res_p (optional)  default detects res and doubles it?  or makes doubel template!
    # mesh_t, mesh_p (optional templates)
    # Plots??  With units....

  return parser.parse_args()

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
  rsrcdir = bindir

  # Get filenames of template input files.
  mapfl_file = rsrcdir+'/mapfl_cor.in'
  print('=> MAPFL input template used for MAS: '+mapfl_file)

  mapfl='mapfl'

  # Change directory to the run directory.
  os.chdir(args.rundir)

  # 1) Trace forwards and backwards between r1 and r0:
  #  - expansion factor at r1 -> expfac_r1_r0.h5
  #  - Make OFM from r0 to r1 -> ofm_r0.h5 (-1, 0 1)
  

  # Setup the PFSS MAPFL tracing:
  print("=> Running MAPFL on MAS solution... ")
  #os.chdir("pfss")
  ierr = os.system('cp '+mapfl_file+' mapfl.in')
  check_error_code(ierr,'Failed on copy of '+mapfl_file+' to mapfl.in')
  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  line_to_check='A field line did not reach'
  check_file_for_line(line_to_check,'mapfl.log','Failed : A field line did not reach R0 or R1.')

  print("=> Calculating the distance to open field boundaries (DCHB)... ")
  ierr = os.system('ch_distance.py -t r1_r0_t.h5 -p r1_r0_p.h5 -force_ch -chfile ofm_r0.h5 -dfile dchb_r1.h5')
  check_error_code(ierr,'Failed on : ch_distance.py -t r1_r0_t.h5 -p r1_r0_p.h5 -force_ch -chfile ofm_r0.h5 -dfile dchb_r1.h5')

  print("    ...done!")
#  os.chdir("..")



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
