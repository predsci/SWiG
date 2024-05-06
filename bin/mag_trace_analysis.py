#!/usr/bin/env python3
import os
import sys
import subprocess
import numpy as np
import argparse
from scipy.interpolate import RegularGridInterpolator
#
import psih5 as ps

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

  # Get path of the rsrc directory where the template 
  # MAPFL input files reside.  
  # Here, assume this script is in the "bin" folder of SWiG.

  bindir = sys.path[0]
  rsrcdir = bindir+'/../rsrc/'

  # Get filenames of template input files.
  pfss_file = rsrcdir+'mapfl_pfss.in'
  cs_file   = rsrcdir+'mapfl_cs.in'  

  mapfl=bindir+'/../mapfl/bin/mapfl'

  # Change directory to the run directory.
  os.chdir(str(args.rundir))

  # 1) Trace PFSS backward from rss to r0:
  #  - theta coords            -> rss_r0_t.h5
  #  - phi coords              -> rss_r0_p.h5
  #  - expansion factor at rss -> expfac_rss_r0.h5
  #  - Make OFM from r0 to rss -> ofm_r0.h5 (-1, 0 1)

  # Setup the PFSS MAPFL tracing:
  print("=> Running MAPFL on PFSS solution... ")
  os.chdir("pfss")
  os.system('cp '+pfss_file+' mapfl.in')
  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  subprocess.run(["bash","-c",Command])
  print("=>    Run complete!")
  os.chdir("..")

  # 2) Trace CS backwards from r1 to rss:
  #  - theta coords -> r1_rss_t.h5
  #  - phi coords   -> r1_rss_p.h5

  # Setup the CS MAPFL tracing:
  print("=> Running MAPFL on CS solution... ")
  os.chdir("cs")
  os.system('cp '+cs_file+' mapfl.in')
  Command=mapfl +' 1>mapfl.log 2>mapfl.err'
  subprocess.run(["bash","-c",Command])
  print("=>    Run complete!")
  os.chdir("..")

  # Read in all required tracing results:
  t_r1_rss,        p_r1_rss,        r1_rss_t      = ps.rdhdf_2d('cs/r1_rss_t.h5')
  _,               _,               r1_rss_p      = ps.rdhdf_2d('cs/r1_rss_p.h5')
  t_br_r1_cs,      p_br_r1_cs,      br_r1_cs      = ps.rdhdf_2d('cs/br_r1_cs.h5')
  t_br_rss_pm_cs,  p_br_rss_pm_cs,  br_rss_pm_cs  = ps.rdhdf_2d('cs/br_rss_pm_cs.h5')
  t_expfac_rss_r0, p_expfac_rss_r0, expfac_rss_r0 = ps.rdhdf_2d('pfss/expfac_rss_r0.h5')

  # Get expansion factor at r1 through interpolation:
  expfac_r1_r0 = slice_tp_tp(t_expfac_rss_r0, p_expfac_rss_r0, expfac_rss_r0, r1_rss_t, r1_rss_p)
  ps.wrhdf_2d('expfac_rss_at_r1.h5', p_r1_rss, t_r1_rss, np.transpose(expfac_r1_r0))

  # Get DCHB at rss:
  os.system(bindir+'/ch_distance.py -v -t pfss/rss_r0_t.h5 -p pfss/rss_r0_p.h5 -force_ch -chfile pfss/ofm_r0.h5 -dfile pfss/dchb_rss.h5')
  t_dchb_rss,      p_dchb_rss,      dchb_rss     = ps.rdhdf_2d('pfss/dchb_rss.h5')

  # Get DCHB at r1 through interpolation:  
  dchb_r1 = slice_tp(t_dchb_rss, p_dchb_rss, dchb_rss, r1_rss_t, r1_rss_p) 
  ps.wrhdf_2d('dchb_at_r1.h5', p_r1_rss, t_r1_rss, np.transpose(dchb_r1))

  # Get Br at r1 with polarity:
  # Make 2D mesh grids of tracing coordinates from r1 to rss:
  mesh_r1_trace_t, mesh_r1_trace_p = np.meshgrid(t_r1_rss,p_r1_rss)

  # Interpolate br_cs_r1 to tracing mesh:
  br_r1_unsigned      = slice_tp(t_br_r1_cs, p_br_r1_cs, br_r1_cs, mesh_r1_trace_t, mesh_r1_trace_p) 

  # Get br_rss mapped to r1:
  br_rss_mapped_to_r1 = slice_tp(t_br_rss_pm_cs, p_br_rss_pm_cs, br_rss_pm_cs, r1_rss_t, r1_rss_p)

  # Use the sign of the mapped br_rss to set the sign of the br_r1:
  polarity_ss_mapped_to_r1 = np.sign(br_rss_mapped_to_r1)
  br_r1 = br_r1_unsigned*polarity_ss_mapped_to_r1
  ps.wrhdf_2d('br_r1.h5', p_r1_rss, t_r1_rss, np.transpose(br_r1))
  
  print('=> Done!')

def slice_tp(t_f,p_f,f,t,p):
  #
  # Extend domain to deal with periodic phi
  #
  p_f_extended, f_extended = extend_periodic_tp(p_f,f)

  interp = RegularGridInterpolator((p_f, t_f), f, bounds_error=False, fill_value=0)
  coords=np.vstack((p, t)).reshape(-1,p.shape[1]*p.shape[0])
  values=(interp((coords.T))).reshape(p.shape)
  return values

def extend_periodic_tp(xvec,data):
  # Detect type of periodicity and return extended data and scale.
  tol=1e-6
  if (np.abs(xvec[-1]-xvec[0]-2*np.pi)<=tol):
    # Assume 1-point overlap...
    data = np.delete(data, 0, 1)
    xvec = np.delete(xvec, 0, 0)
  elif ((xvec[-1]-xvec[0])>2*np.pi+tol and \
        (xvec[-2]-xvec[1])<2*np.pi-tol):
    # Assume 2-point overlap...
    data = np.delete(data, 0, 1)
    xvec = np.delete(xvec, 0, 0)
    data = np.delete(data, len(xvec)-1, 1)
    xvec = np.delete(xvec, len(xvec)-1, 0)
  data = np.append(data,np.append(data,data,1),1)
  xvec = np.append(xvec-2*np.pi,np.append(xvec,xvec+2*np.pi))
  return xvec,data

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
