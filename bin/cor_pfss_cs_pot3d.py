#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess
from pathlib import Path
#
import psi_io as ps

########################################################################
#  COR_PFSS_CS_POT3D: Coronal magnetic field PFSS+CS model using POT3D 
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
  parser = argparse.ArgumentParser(description='Generate PFSS and CS solutions given an input magnetic full-Sun map.')

  parser.add_argument('br_input_file',
    help='Br map input file',
    type=str)

  parser.add_argument('-np',
    help='Number of MPI processes (ranks)',
    dest='np',
    type=int,
    default=1,
    required=False)

  parser.add_argument('-gpu',
    help='Set flag -gpu to use ifprec=1.',
    dest='gpu',
    action='store_true',
    default=False,
    required=False)

  parser.add_argument('-rss',
    help='Specify the rss distance (default=2.5).',
    dest='rss',
    type=float,
    default=2.5,
    required=False)

  parser.add_argument('-r1',
    help='Specify the r1 distance (default=21.5).',
    dest='r1',
    type=float,
    default=21.5,
    required=False)


  return parser.parse_args()

def run(args):

  print('===========================')
  print('===========================')
  print('=> Starting PFSS+CS model')
  print('===========================')
  print('===========================')

  # Get path of the rsrc directory where the template 
  # POT3D input files reside.  
  # Here, assume this script is in the "bin" folder of SWiG.
  rsrcdir = sys.path[0]+'/../rsrc/'
  
  # Get filenames of template input files.
  pfss_file = rsrcdir+'pot3d_pfss.dat'
  cs_file   = rsrcdir+'pot3d_cs.dat'

  # Get full path of input file:
  br_input_file = str(Path(args.br_input_file).resolve())

  print('=> Input magnetic map:                 '+br_input_file)
  print('=> POT3D input template used for PFSS: '+pfss_file)
  print('=> POT3D input template used for CS:   '+cs_file)

  pot3d=sys.path[0]+'/../pot3d/bin/pot3d'

  # Some error checking:
  check_error_code(float(args.rss) <= 1.0,'ERROR: rss must be greather than 1.')
  check_error_code(float(args.rss) >= float(args.r1),'ERROR: r1 must be greater than rss.')

  # Setup the PFSS run.
  print("=> Making directory to run PFSS: pfss")
  os.makedirs("pfss", exist_ok=True)

  print("=> Copying input file template and input map to pfss directory...")
  ierr = os.system('cp '+pfss_file+' pfss/pot3d.dat') 
  check_error_code(ierr,'Failed on copy of '+pfss_file+' to pfss/pot3d.dat')
  # Read in input map and write it in tp for use with POT3D:
  xvec,yvec,data = ps.rdhdf_2d(br_input_file)
  if (np.max(xvec) > 3.5):
    tvec = yvec
    pvec = xvec
    data = np.transpose(data)
  else:
    tvec = xvec
    pvec = yvec

  Command='grep "nt=" pfss/pot3d.dat'
  ierr = subprocess.run(["bash","-c",Command],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL, text=True)
  check_error_code(ierr.returncode,'Failed to get "nt=" from pfss/pot3d.dat')
  pot3d_nt=int(ierr.stdout.split('=')[1])
  Command='grep "np=" pfss/pot3d.dat'
  ierr = subprocess.run(["bash","-c",Command],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL, text=True)
  check_error_code(ierr.returncode,'Failed to get "np=" from pfss/pot3d.dat')
  pot3d_np=int(ierr.stdout.split('=')[1])

  if len(tvec)/pot3d_nt > 0.05 and len(pvec)/pot3d_np > 0.05:
    print(' ')
    print('====> WARNING!!!!! ')
    print("====> The t and p dimentions in the input map are more than 5% larger than the resolutions of t and p set in the pot3d.dat template file for PFSS ")
    print('====> Please check the processing of the map.')
    print(' ')
  elif len(pvec)/pot3d_np > 0.05:
    print(' ')
    print('====> WARNING!!!!! ')
    print("====> The p dimenion in the input map is more than 5% larger than the resolution of p set in the pot3d.dat template file for PFSS ")
    print('====> Please check the processing of the map.')
    print(' ')
  elif len(tvec)/pot3d_nt > 0.05:
    print(' ')
    print('====> WARNING!!!!! ')
    print("====> The t dimenion in the input map is more than 5% larger than the resolution of t set in the pot3d.dat template file for PFSS ")
    print('====> Please check the processing of the map.')

  ps.wrhdf_2d('pfss/br_input_tp.h5',tvec,pvec,data)
    
  print("=> Entering pfss directory and modifying input file... ")
  os.chdir("pfss")
  sed('r1',str(args.rss),'pot3d.dat')
  if (args.gpu):
    sed('ifprec','1','pot3d.dat')

  print("=> Running POT3D for PFSS...")
  Command='mpiexec -np '+str(args.np)+' '+pot3d +' 1>pot3d.log 2>pot3d.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  print("    ...done!")
  
  # Create input for CS. Here, we assume no overlap between PFSS 
  # and CS so we just take the outer slice.
  rvec_pfss, tvec_pfss, pvec_pfss, data_pfss = ps.rdhdf_3d('br_pfss.h5')
  ps.wrhdf_2d('br_rss.h5', tvec_pfss, pvec_pfss, data_pfss[:,:,-1])
  os.chdir("..")

  # Set up the CS run.
  print("=> Making directory to run CS: cs")
  os.makedirs("cs", exist_ok=True)
  print("=> Copying input file template and input map to cs directory...")
  ierr = os.system('cp '+cs_file+' cs/pot3d.dat')
  check_error_code(ierr,'Failed on copy of '+cs_file+' to cs/pot3d.dat')
  ierr = os.system('cp pfss/br_rss.h5 cs/')
  check_error_code(ierr,'Failed on copy of pfss/br_rss.h5 to cs/')
  print("=> Entering cs directory and modifying input file... ")
  os.chdir("cs")
  sed('r0',str(args.rss),'pot3d.dat')
  sed('r1',str(args.r1),'pot3d.dat')
  if (args.gpu):
    sed('ifprec','1','pot3d.dat')

  # CS POT3D
  print("=> Running POT3D for CS...")
  Command='mpiexec -np '+str(args.np)+' '+pot3d +' 1>pot3d.log 2>pot3d.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  print("    ...done!")
  
  # Extract (unsigned) outer slice of CS Br for later use.
  rvec_cs, tvec_cs, pvec_cs, data_cs = ps.rdhdf_3d('br_cs.h5')
  ps.wrhdf_2d('br_r1_cs.h5', tvec_cs, pvec_cs, data_cs[:,:,-1])
  os.chdir("..")
  
  print('===========================')
  print('===========================')
  print('=> PFSS+CS model complete!')
  print('===========================')
  print('===========================')
  
  # Merge the two runs [NOT NEEDED FOR NOW - MAYBE LATER]
  #print("=> Merging two runs")
  #concate3D_dim2('pfss/br_pfss.h5','cs/br_cs.h5','br_pfsscs.h5',-1)
  #concate3D_dim2('pfss/bt_pfss.h5','cs/bt_cs.h5','bt_pfsscs.h5',-2)
  #concate3D_dim2('pfss/bp_pfss.h5','cs/bp_cs.h5','bp_pfsscs.h5',-2)

#def concate3D_dim2(file1,file2,file3,dl):
#  rvec1, tvec1, pvec1, data1   = ps.rdhdf_3d(file1)
#  rvec2, tvec2, pvec2, data2   = ps.rdhdf_3d(file2)
#  data1 = np.array(data1)
#  data2 = np.array(data2)
#  data = np.concatenate([data1[:,:,0:dl],data2], axis=2)
#  rvec = np.concatenate([rvec1[0:dl],rvec2])
#  ps.wrhdf_3d(file3, rvec, tvec1, pvec1, data)

def sed(match,value,file):
  ierr = os.system('sed -i "s/.*'+match+'=.*/  '+match+'='+value+'/" "'+file+'"')
  check_error_code(ierr,'Failed on sed of '+match+' in '+file)


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
########################################################################
