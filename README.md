<img width=500 src="swig_logo.png" alt="SwiG" />  
  
# SWiG: Solar Wind Generator  

[Predictive Science Inc.](https://www.predsci.com)  
 
--------------------------------  
  
## OVERVIEW  
`SWiG` is a python code that generates emperical solar wind solutions (WSA or DCHB) using potential field source surface (PFSS) and current sheet (CS) models of the coronal magnetic field.
  
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
  
Once you have the SWiG repository with its submodules, follow the instructions in each submodule to install them.  Then, add the SWiG `bin` folder to your PATH.  For example, with bash:  
```
export PATH=<LOCATION_OF_SWIG>/bin:$PATH
```
  
--------------------------------  
  

## HOW TO RUN SWiG  
  
Run the main script `swig.py` with the desired options:  
```
usage: swig.py [-h] [-oidx OIDX] [-rundir RUNDIR] [-np NP] [-gpu] [-sw_model SW_MODEL] [-rss RSS] [-r1 R1] [-noplot] input_map

positional arguments:
  input_map           Input Br full-Sun magnetogram (h5).

optional arguments:
  -h, --help          show this help message and exit
  -oidx OIDX          Index to use for output file names).
  -rundir RUNDIR      Directory where run will go.
  -np NP              Number of MPI processes (ranks)
  -gpu                Indicate that POT3D will be run on GPUs.
  -sw_model SW_MODEL  Select solar wind model.
  -rss RSS            Set source surface radius (default 2.5 Rs).
  -r1 R1              Set outer radius (default 21.5 Rs).
  -noplot             Do not plot results
```
  
It is highly recommended to process your Br map using the tools included in our Open-source Flux Transport model [OFT](https;//github.com/predsci/oft) before using the map in SWiG.  

--------------------------------  
 
