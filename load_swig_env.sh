#!/bin/bash

# Script to load SWiG environment.
# This script sets all the paths to the SWiG and its submodule executables.

# To use this script, source it in your BASH terminal with:
#   . load_swig_env.sh

# You should then have all executables and scripts in your path,
# allowing you to run SWiG.
# Note - this assumes you have followed the instructions in each submodule
#        to build/compile each submodule.

cR="\033[1;31m"
cG="\033[32m"
cX="\033[0m"
echo="echo -e"

${echo} "${cG}==> SWiG Environment Setup${cX}"

(return 0 2>/dev/null) && sourced=1 || sourced=0

if [ $sourced -eq "0" ]
then
  ${echo} "${cR}==> ERROR! It seems this script was executed instead of being sourced.${cX}"
  ${echo} "${cR}    Please source this script with: '. load_swig_env.sh'${cX}"
  exit 1
fi

swig_dir="$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )"

echo "==> Checking that submodule components are installed..."
if [ ! -e ${swig_dir}/pot3d/bin/pot3d ]
then
  ${echo} "${cR}==> ERROR! POT3D does not seem to be built!${cX}"
  ${echo} "${cR}    Please ensure the submodule was checked out and build the code.${cX}"
  exit 1
fi

if [ ! -e ${swig_dir}/mapfl/bin/mapfl ]
then
  ${echo} "${cR}==> ERROR! MAPFL does not seem to be built!${cX}"
  ${echo} "${cR}    Please ensure the submodule was checked out and build the code.${cX}"
  exit 1
fi

echo "==> Appending SWiG and its submodules located at [${swig_dir}] to PATH..."

export PATH=${swig_dir}:${swig_dir}/bin:${swig_dir}/pot3d/bin:${swig_dir}/mapfl/bin:$PATH

${echo} "${cG}==> Done!${cX}"

