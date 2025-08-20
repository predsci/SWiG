<img width=500 src="swig_logo.png" alt="SwiG" />  
  
# SWiG: Solar Wind Generator  

[Predictive Science Inc.](https://www.predsci.com)  
 
--------------------------------  
  
## OVERVIEW  
`SWiG` is a code pacakge that generates emperical solar wind solutions (WSA or DCHB) using potential field source surface (PFSS) and current sheet (CS) models of the coronal magnetic field.
  
SWiG includes the potential field solver [POT3D](https;//github.com/predsci/pot3d) and the field line tracer [MapFL](https;//github.com/predsci/mapfl) as submodules.
  
--------------------------------  
  

## HOW TO BUILD SWiG  

Check out the repository using git's `recursive` option:  

```
git clone https://github.com/predsci/swig --recursive
```
If forgotten, initialize the submodules with:  
```
git submodule update --init
```
When pulling updates, to ensure you get the submodule updates as well, use:  
```
git pull --recurse-submodules
```
  
Once you have the SWiG repository with its submodules, follow the instructions in each submodule to build them.  
  
All executables/scripts need to be in your PATH for SWiG to work.  
For BASH, we have provided a script that can be sourced to do this:
```
. ./load_swig_env.sh
```
The script can also be used as a reference for making an equivalent script for other shells.
  
--------------------------------  
  

## HOW TO RUN SWiG  
  
First, make sure all SWiG tools and scripts are in your PATH (see above).  
  
Next, for many input Br maps, it is recommended to process the maps using the map processing tools included in our Open-source Flux Transport model [OFT](https;//github.com/predsci/oft) before using them in SWiG.  
  
Run the main script `swig.py` with the desired options:  
```
usage: swig.py [-h] [-oidx OIDX] [-rundir RUNDIR] [-np NP] [-sw_model SW_MODEL] [-rss RSS] [-r1 R1] [-noplot] input_map

positional arguments:
  input_map           Input Br full-Sun magnetogram (h5).

optional arguments:
  -h, --help          show this help message and exit
  -oidx OIDX          Index to use for output file names).
  -rundir RUNDIR      Directory where run will go.
  -np NP              Number of MPI processes (ranks)
  -sw_model SW_MODEL  Select solar wind model.
  -rss RSS            Set source surface radius (default 2.5 Rs).
  -r1 R1              Set outer radius (default 21.5 Rs).
  -noplot             Do not plot results
```  
When the run is complete, the directory where the results can be found will be displayed.  

--------------------------------  
 
