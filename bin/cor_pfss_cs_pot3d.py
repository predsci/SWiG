#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
import subprocess
#
import psi_io as ps

########################################################################
#  COR_PFSS_CS_POT3D 
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

  # Get path of the rsrc directory where the template 
  # POT3D input files reside.  
  # Here, assume this script is in the "bin" folder of SWiG.

  rsrcdir = sys.path[0]+'/../rsrc/'
  
  # Get filenames of template input files.
  pfss_file = rsrcdir+'pot3d_pfss.dat'
  cs_file   = rsrcdir+'pot3d_cs.dat'

  # Get filename of input map.
  br_input_file=args.br_input_file

  print('PFSS input template used : '+pfss_file)
  print('CS   input template used : '+cs_file)
  print('Input Magnetic Map used  : '+br_input_file)

  pot3d=sys.path[0]+'/../pot3d/bin/pot3d'

  if float(args.rss) <= 1.0:
    print("ERROR: rss must be greather than 1.")
    return
  if float(args.rss) >= float(args.r1):
    print("ERROR: r1 must be greater than rss.")
    return

  # Setup the PFSS run.
  print("=> Making PFSS directory ")
  os.makedirs("pfss", exist_ok=True)
  os.system('cp '+pfss_file+' pfss/pot3d.dat')
  
  xvec,yvec,data = ps.rdhdf_2d(br_input_file)
  if (np.max(xvec) > 3.5):
    tvec = yvec
    pvec = xvec
    data = np.transpose(data)
  else:
    tvec = xvec
    pvec = yvec
  ps.wrhdf_2d('pfss/br_input_tp.h5',tvec,pvec,data)
    
  print("=> Entering pfss directory ")
  os.chdir("pfss")
  sed('r1',str(args.rss),'pot3d.dat')
  if (args.gpu):
    sed('ifprec','1','pot3d.dat')

  # Launch the PFSS run with POT3D.
  print("=> Running POT3D for PFSS")
  Command='mpiexec -np '+str(args.np)+' '+pot3d +' 1>pot3d.log 2>pot3d.err'
  subprocess.run(["bash","-c",Command])
  print("=>    Run complete!")
  
  # Create input for CS.
  # Here, we assume no overlap between PFSS and CS so we just take the 
  # outer slice.
  rvec_pfss, tvec_pfss, pvec_pfss, data_pfss = ps.rdhdf_3d('br_pfss.h5')
  ps.wrhdf_2d('br_rss.h5', tvec_pfss, pvec_pfss, data_pfss[:,:,-1])
  os.chdir("..")

  # Set up the CS run.
  print("=> Making CS directory ")
  os.makedirs("cs", exist_ok=True)
  os.system('cp '+cs_file+' cs/pot3d.dat')
  os.system('cp pfss/br_rss.h5 cs/')
  print("=> Entering cs directory ")
  os.chdir("cs")
  sed('r0',str(args.rss),'pot3d.dat')
  sed('r1',str(args.r1),'pot3d.dat')
  if (args.gpu):
    sed('ifprec','1','pot3d.dat')

  # CS POT3D
  print("=> Running POT3D for CS")
  Command='mpiexec -np '+str(args.np)+' '+pot3d +' 1>pot3d.log 2>pot3d.err'
  subprocess.run(["bash","-c",Command])
  print("=>    Run complete!")
  
  # Extract (unsigned) outer slice of CS Br for later use.
  rvec_cs, tvec_cs, pvec_cs, data_cs = ps.rdhdf_3d('br_cs.h5')
  ps.wrhdf_2d('br_r1_cs.h5', tvec_cs, pvec_cs, data_cs[:,:,-1])
  os.chdir("..")
  
  print("All done!")
  
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
  os.system('sed -i "s/.*'+match+'=.*/  '+match+'='+value+'/" "'+file+'"')

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
