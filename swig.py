#!/usr/bin/env python3

# SWiG:  Solar Wind Generato
#        Generate solar wind quantities using PFSS+CS magnetic fields combined
#        with emperical solar wind models.




#  Add option to plot everything using plot2d, etc.

# Get runname and make folder.
# Inside make a results folder for the solar wind and other quatities.










# FORTRAN TOOLS NEEDED:
# 1) POT3D         [github]
# 2) MAPFL         [github]
# 3) SLICE         [?  Maybe convert to py?]

#Output: verbose level is V#
# V0  2D Solar wind and field at r1 (rho, vr, temp, br)
# V0  2D Br at Rss and R0
# V0  2D Open Field (CH) map at r0
# V0  Meta data file with actual rss, r1, etc. values
# V1  3D PFSS and CS fields (CS field with polarity)
# V2  2D Expansion factors and distance to OF boundaries at r0, rss, and r1

# Input: Required vs Optional
#  Required:
#   br file (does not further process it - so assumes final map - auto transpose, auto sinlat detection)
#  Optional:
#   r0  : (default 1) lower radius for OF tracing and expansion factor (able to compinsate for high res data)
#   rss : (default 2.5) rss radius (default r resolutions based on 2.5...)
#   rss overlap??   Make PFSS rss be rss+overlap, than extract rss slice (interp?)
#   r1  : (default 21.5) outer radius for solar wind data calucaltion and outer radius of CS model
#   gridstyle : psi vs wsa : Determines tracing grid..  maybe have this be pt grid template instead?
#   mapping_res_multiplier : resoluton of mapping (default is 2x)?
#   verbosity : output level V0, V1, V2
#   plot on/off (default on) : Decide to plot all 2D quantities or not
#   

#  cor_pfss_cs_pot3d.py
#  mag_trace_analysis.py
#  eswim.py






