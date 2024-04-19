#!/usr/bin/env python3
import os
import sys
import numpy as np
import argparse
#
import psih5 as ps

#######################
#  MAG_TRACE_ANALYSIS #
#######################

# INPUT:   Directory of run (where PFSS and CS were done)
#          [also r1 and rss for mapfl inputs]
# OUTPUT:  expfac_r1.h5, dchb_r1.h5  (for solar wind models)
#          ofm.h5, slogq_r0.h5, etc. bonus.. 

def argParsing():
  parser = argparse.ArgumentParser(description='Generate PFSS and CS solutions given an input magnetic full-Sun map.')

  parser.add_argument('rundir',
    help='Directory of run (where PFSS and CS were computed)',
    type=str)
    
  parser.add_argument('-mapfl_exe',
    help='Full path to MAPFL executable (otherwise use relative path to mapfl in swig).',
    dest='mapfl',
    type=str,
    required=False)    

  return parser.parse_args()

def run(args):

  # Get path of the rsrc directory where the template 
  # MAPFL input files reside.  
  # Here, assume this script is in the "bin" folder of SWiG.

  bindir = sys.path[0]
  rsrcdir = bindir+'/../rsrc/'

  # Get filenames of template input files.
  pfss_file = rsrcdir+'mapfl_pfss.in'
  cs_file = rsrcdir+'mapfl_cs.in'  

  if args.mapfl is not None:
      mapfl=args.mapfl
  else:
      mapfl=bindir+'/../mapfl/bin/mapfl'

  #mapfl=args.mapfl if args.mapfl else os.popen('which mapfl').read().replace('\n','')
  # Some basic error checking:
  #if [check if mapfl is really there]
  #  print("ERROR:  MAPFL is not in the path.")
  #  return  

  # Change directory to the run directory.
  os.chdir(str(args.rundir))

  # 1) Trace PFSS backward from rss to r0:
  #  - theta coords            -> rss_r0_t.h5
  #  - phi coords              -> rss_r0_p.h5
  #  - expansion factor at rss -> expfac_rss_r0.h5
  #  - Make OFM from r0 to rss -> ofm.h5 (-1, 0 1)

  # Setup the PFSS MAPFL tracing.
  print("=> Running MAPFL on PFSS solution... ")
  os.chdir("pfss")
  os.system('cp '+pfss_file+' mapfl.in')
  #sed('rss',str(args.rss),'mapfl.in')
  os.system(mapfl +' 1>mapfl.log 2>mapfl.err')
  # [ADD ERROR CHECK HERE]
  print("=> Run complete!")
  os.chdir("..")

  # 2) Trace CS backwards from r1 to rss:
  #  - theta coords -> r1_rss_t.h5
  #  - phi coords   -> r1_rss_p.h5

  # Setup the CS MAPFL tracing.
  print("=> Running MAPFL on CS solution... ")
  os.chdir("cs")
  os.system('cp '+cs_file+' mapfl.in')
  #sed('rss',str(args.rss),'mapfl.in')
  os.system(mapfl +' 1>mapfl.log 2>mapfl.err')
  # [ADD ERROR CHECK HERE]
  print("=> Run complete!")
  os.chdir("..")

# 4) Get expansion factor at r1 through interpolation:
#    [THIS IS SHADY...  SHOULD GET EXP FOR R1->RSS AND MULTIPLY???]
#    [OR IS WSA TUNED TO EXPFAC AT RSS?]
  os.system('slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 pfss/expfac_rss_r0.h5 expfac_r1_r0.h5')

# 5) Get DCHB at rss:
  os.system(bindir+'/ch_distance.py -v -t pfss/rss_r0_t.h5 -p pfss/rss_r0_p.h5 -force_ch -chfile pfss/ofm.h5 -dfile dchb_rss.h5')

# 6) Interpolate to get DCHB at r1:
  os.system('slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 dchb_rss.h5 dchb_r1.h5')

# 7) Get Br at r1 with polarity:
#    - Get r1 tracing mesh scales in 2D:
  tvec,pvec,f=ps.rdhdf_2d('cs/r1_rss_t.h5')
  t2d,p2d=np.meshgrid(tvec,pvec)
  ps.wrhdf_2d('mesh_r1_trace_t.h5',tvec,pvec,t2d)
  ps.wrhdf_2d('mesh_r1_trace_p.h5',tvec,pvec,p2d) 

#    - Interpolate br_cs_r1 to tracing mesh:
  os.system('slice -v -x mesh_r1_trace_t.h5 -y mesh_r1_trace_p.h5 cs/br_r1_cs.h5 br_r1_unsigned.h5')

#    - Get br_rss mapped to r1:
  os.system('slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 cs/br_rss_pm_cs.h5 br_rss_mapped_to_r1.h5')

#    - Use the sign of the mapped br_rss to set the sign of the br_r1:
#      [THIS SHOULD BE PYTHON]
  os.system('sds_func -func sign -x br_rss_mapped_to_r1.h5 polarity_ss_mapped_to_r1.h5')
  os.system('sds_func -func ''ax*y+b'' -x br_r1_unsigned.h5 -y polarity_ss_mapped_to_r1.h5 br_r1.h5')  
  
  print('Done!')

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
