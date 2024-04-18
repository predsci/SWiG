#!/usr/bin/env python3

# Need to do steps that CORHEL does.

# INPUT:   Directories of PFSS and CS runs, RSRC folder with mapfl input files.
# OUTPUT:  expfac_r1.h5, dchb_r1.h5  (for solar wind models)
#          ofm.h5, slogq_r0.h5, etc. bonus.. + PLOTS

# Two options?:  1) single B grid (MAS run)  2) PFSS+CS 

#(1) and (2)+(3) are mapfl runs.

# 1) Trace CS backwards from r1 to rss:
#    - theta coords -> r1_rss_t.h5
#    - phi coords   -> r1_rss_p.h5
# 2) Trace PFSS backward from rss to r0:
#    - theta coords            -> rss_r0_t.h5
#    - phi coords              -> rss_r0_p.h5
#    - expansion factor at rss -> expfac_rss_r0.h5
# 3) Make PFSS OFM from r0 to rss -> ofm.h5 (-1, 0 1)

# 4) Get expansion factor at r1 through interpolation:
#    [THIS IS SHADY...  SHOULD GET EXP FOR R1->RSS AND MULTIPLY???]
#    [OR IS WSA TUNED TO EXPFAC AT RSS?]
#    slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 pfss/expfac_rss_r0.h5 expfac_r1_r0.h5

# 5) Get DCHB at rss:
#    ch_distance.py -v -t rss_r0_t.h5 -p rss_r0_p.h5 -force_ch ofm.h5 dchb_rss.h5

# 6) Interpolate to get DCHB at r1:
#    slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 dchb_rss.h5 dchb_r1.h5"

# 7) Get Br at r1 with polarity:
#    - Get r1 tracing mesh scales in 2D:
#      tvec,pvec,f=ps.rdhdf_2d('cs/r1_rss_t.h5')
#      t2d,p2d=np.meshgrid(tvec,pvec)
#      ps.wrhdf_2d('mesh_r1_trace_t.h5',tvec,pvec,t2d)
#      ps.wrhdf_2d('mesh_r1_trace_p.h5',tvec,pvec,p2d) 

#    - Interpolate br_cs_r1 to tracing mesh:
#      slice -v -x mesh_r1_trace_t.h5 -y mesh_r1_trace_p.h5 cs/br_r1_cs.h5 br_r1_unsigned.h5

#    - Get br_rss mapped to r1:
#      slice -v -x cs/r1_rss_t.h5 -y cs/r1_rss_p.h5 cs/br_rss_pm_cs.h5 br_rss_mapped_to_r1.h5

#    - Use the sign of the mapped br_rss to set the sign of the br_r1:
#      [THIS SHOULD BE PYTHON]
#      sds_func -func sign -x br_rss_mapped_to_r1.h5 polarity_ss_mapped_to_r1.h5
#      sds_func -func 'ax*y+b' -x br_r1_unsigned.h5 -y polarity_ss_mapped_to_r1.h5 br_r1.h5


