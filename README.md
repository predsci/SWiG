<img width=500 src="swig_logo.png" alt="SwiG" />  
  
# SWiG: Solar Wind Generator  

[Predictive Science Inc.](https://www.predsci.com)  
 
--------------------------------  
  
## OVERVIEW  
`SWiG` is a code pacakge that generates emperical solar wind   
solutions (WSA or DCHB) using potential field source surface  
(PFSS) and current sheet (CS) models of the coronal magnetic field.
  
SWiG includes the potential field solver [POT3D](https;//github.com/predsci/pot3d)  
and the field line tracer [MapFL](https;//github.com/predsci/mapfl) as submodules.
  
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
usage: swig.py input_map [-h] [-oidx OIDX] [-rnum RNUM] 
                         [-rundir RUNDIR] [-np NP] [-sw_model SW_MODEL]
                         [-sw_model_params SW_MODEL_PARAMS] [-rss RSS] 
                         [-r1 R1] [-r0_trace R0_TRACE] [-noplot] 

positional arguments:
  input_map             Input Br full-Sun magnetogram (h5).

optional arguments:
  -h, --help            Show this help message and exit
  -oidx                 Index to use for output file names.
  -rnum                 Realization number to use for output file names (Default None).
  -rundir               Directory where run will go.
  -np                   Number of MPI processes (ranks)
  -sw_model             Select solar wind model (Options: wsa, wsa2, psi)
  -sw_model_params      Flags to pass to the solar wind model generation script eswim.py.
                        WSA2: -vslow <#> -vfast <#> -c1 <#> -c2 <#> -c3_i <#> -c4 <#> -c5 <#>
                        WSA:  -vslow <#> -vfast <#> -c1 <#> -c2 <#> -c3_i <#> -c4 <#> -vmax <#>
                        PSI:  -vslow <#> -vfast <#> -psi_eps <#> -psi_width <#> 
                        For all models:
                        -rhofast <#> -tfast <#>
  -rss                  Set source surface radius (default 2.5 Rs).
  -r1                   Set outer radius (default 21.5 Rs).
  -r0_trace             Set inner radius to trace field lines to/from (default is 1.0 Rs).
  -noplot               Do not plot results
```  
When the run is complete, the directory where the results can be found will be displayed.  

--------------------------------  
 
