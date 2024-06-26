#!/usr/bin/env python3
import os
import sys
import subprocess
import numpy as np
import argparse
from scipy.interpolate import RegularGridInterpolator
#
import psi_io as ps

########################################################################
#  MAG_TRACE_ANALYSIS #
########################################################################
#
# INPUT:   Directory of run (where PFSS and CS were done)
# OUTPUT:  expfac_rss_at_r1.h5, dchb_at_r1.h5  (for solar wind models)
#          ofm_r0.h5, slogq_r0.h5 (for plotting/analysis) 
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
  parser = argparse.ArgumentParser(description='Generate PFSS and CS solutions given an input magnetic full-Sun map.')

  parser.add_argument('rundir',
    help='Directory of run (where PFSS and CS were computed)',
    type=str)   

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
  rsrcdir = bindir+'/../rsrc/'

  # Get filenames of template input files.
  pfss_file = rsrcdir+'mapfl_pfss.in'
  cs_file   = rsrcdir+'mapfl_cs.in'  
  print('=> MAPFL input template used for PFSS: '+pfss_file)
  print('=> MAPFL input template used for CS:   '+cs_file)

  mapfl=bindir+'/../mapfl/bin/mapfl'

  # Change directory to the run directory.
  os.chdir(args.rundir)

  # 1) Trace PFSS backward from rss to r0:
  #  - theta coords            -> rss_r0_t.h5
  #  - phi coords              -> rss_r0_p.h5
  #  - expansion factor at rss -> expfac_rss_r0.h5
  #  - Make OFM from r0 to rss -> ofm_r0.h5 (-1, 0 1)

  # Setup the PFSS MAPFL tracing:
  print("=> Running MAPFL on PFSS solution... ")
  os.chdir("pfss")
  ierr = os.system('cp '+pfss_file+' mapfl.in')
  check_error_code(ierr,'Failed on copy of '+pfss_file+' to mapfl.in')
  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  line_to_check='A field line did not reach'
  check_file_for_line(line_to_check,'mapfl.log','Failed : A field line did not reach R0 or R1.')

  print("    ...done!")
  os.chdir("..")

  # 2) Trace CS backwards from r1 to rss:
  #  - theta coords -> r1_rss_t.h5
  #  - phi coords   -> r1_rss_p.h5

  # Setup the CS MAPFL tracing:
  print("=> Running MAPFL on CS solution...")
  os.chdir("cs")
  ierr = os.system('cp '+cs_file+' mapfl.in')
  check_error_code(ierr,'Failed on copy of '+cs_file+' to mapfl.in')
  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  print('   Command: '+Command)
  ierr = subprocess.run(["bash","-c",Command])
  check_error_code(ierr.returncode,'Failed : '+Command)
  line_to_check='A field line did not reach'
  check_file_for_line(line_to_check,'mapfl.log','Failed : A field line did not reach R0 or R1.')

  print("    ...done!")
  os.chdir("..")

  print("=> Reading in trace results for processing...")
  # Read in all required tracing results:
  t_r1_rss,        p_r1_rss,        r1_rss_t      = ps.rdhdf_2d('cs/r1_rss_t.h5')
  _,               _,               r1_rss_p      = ps.rdhdf_2d('cs/r1_rss_p.h5')
  t_br_r1_cs,      p_br_r1_cs,      br_r1_cs      = ps.rdhdf_2d('cs/br_r1_cs.h5')
  t_br_rss_pm_cs,  p_br_rss_pm_cs,  br_rss_pm_cs  = ps.rdhdf_2d('cs/br_rss_pm_cs.h5')
  t_expfac_rss_r0, p_expfac_rss_r0, expfac_rss_r0 = ps.rdhdf_2d('pfss/expfac_rss_r0.h5')

  print("=> Projecting expansion factor at RSS out to R1...")
  # Get expansion factor at r1 through interpolation:
  expfac_r1_r0 = slice_tp(t_expfac_rss_r0, p_expfac_rss_r0, expfac_rss_r0, r1_rss_t, r1_rss_p)
  ps.wrhdf_2d('expfac_rss_at_r1.h5', p_r1_rss, t_r1_rss, np.transpose(expfac_r1_r0))
  print("   ...wrote file: expfac_rss_at_r1.h5")

  print("=> Calculating the distance to open field boundaries (DCHB)... ")
  print("   (automatically projecting DCHB at R0 to RSS)")
  # Get DCHB at rss:
  ierr = os.system(bindir+'/ch_distance.py -t pfss/rss_r0_t.h5 -p pfss/rss_r0_p.h5 -force_ch -chfile pfss/ofm_r0.h5 -dfile pfss/dchb_rss.h5')
  check_error_code(ierr,'Failed on : '+bindir+'/ch_distance.py -t pfss/rss_r0_t.h5 -p pfss/rss_r0_p.h5 -force_ch -chfile pfss/ofm_r0.h5 -dfile pfss/dchb_rss.h5')
  t_dchb_rss,      p_dchb_rss,      dchb_rss     = ps.rdhdf_2d('pfss/dchb_rss.h5')

  print("=> Projecting DCHB at RSS out to R1...")
  # Get DCHB at r1 through interpolation:  
  dchb_r1 = slice_tp(t_dchb_rss, p_dchb_rss, dchb_rss, r1_rss_t, r1_rss_p) 
  ps.wrhdf_2d('dchb_at_r1.h5', p_r1_rss, t_r1_rss, np.transpose(dchb_r1))
  print("   ...wrote file: dchb_at_r1.h5")

  print("=> Using RSS->R1 tracings to assign polarity to CS Br at R1...")
  # Make 2D mesh grids of tracing coordinates from r1 to rss:
  mesh_r1_trace_t, mesh_r1_trace_p = np.meshgrid(t_r1_rss,p_r1_rss)
  # Interpolate br_cs_r1 to tracing mesh:
  br_r1_unsigned = slice_tp(t_br_r1_cs, p_br_r1_cs, br_r1_cs, mesh_r1_trace_t, mesh_r1_trace_p) 
  # Get br_rss mapped to r1:
  br_rss_mapped_to_r1 = slice_tp(t_br_rss_pm_cs, p_br_rss_pm_cs, br_rss_pm_cs, r1_rss_t, r1_rss_p)
  # Use the sign of the mapped br_rss to set the sign of the br_r1:
  polarity_ss_mapped_to_r1 = np.sign(br_rss_mapped_to_r1)
  br_r1 = br_r1_unsigned*polarity_ss_mapped_to_r1
  ps.wrhdf_2d('br_r1.h5', p_r1_rss, t_r1_rss, np.transpose(br_r1))
  print("   ...wrote file: br_r1.h5")
  
  print('===========================================')
  print('===========================================')
  print('=> Magnetic field trace analysis complete!')
  print('===========================================')
  print('===========================================')

def slice_tp(t_f,p_f,f,t,p):
  # Extend domain to deal with periodic phi
  p_f_extended, f_extended = extend_periodic_tp(p_f,f)

  interp = RegularGridInterpolator((p_f_extended, t_f), f_extended, bounds_error=False, fill_value=0)
  coords=np.column_stack((p.flatten(), t.flatten()))
  values=(interp((coords))).reshape(p.shape)
  return values

def extend_periodic_tp(xvec,data):
  # Detect type of periodicity and return extended data and scale.
  tol=1e-6
  if (np.abs(xvec[-1]-xvec[0]-2*np.pi)<=tol):
    # Assume 1-point overlap...
    data = np.delete(data, 0, 0)
    xvec = np.delete(xvec, 0, 0)
  elif ((xvec[-1]-xvec[0])>2*np.pi+tol and (xvec[-2]-xvec[1])<2*np.pi-tol):
    # Assume 2-point overlap...
    data = np.delete(data, 0, 0)
    xvec = np.delete(xvec, 0, 0)
    data = np.delete(data, len(xvec)-1, 0)
    xvec = np.delete(xvec, len(xvec)-1, 0)
  data = np.append(data,np.append(data,data,0),0)
  xvec = np.append(xvec-2*np.pi,np.append(xvec,xvec+2*np.pi))
  return xvec,data

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
