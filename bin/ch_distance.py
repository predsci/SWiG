#!/usr/bin/env python3
import argparse
import numpy as np
from scipy.interpolate import RegularGridInterpolator
#
import psih5 as ps

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
  parser = argparse.ArgumentParser(description='Compute the distance to the nearest coronal hole boundary.')

  parser.add_argument('-v',
    help='Set flag -v to turn on verbose mode.',
    dest='verbose',
    action='store_true',
    default=False,
    required=False)

  parser.add_argument('-dp',
    help='Set flag -dp to display progress as the calculation proceeds.',
    dest='show_progress',
    action='store_true',
    default=False,
    required=False)

  parser.add_argument('-cfval',
    help='Use -cfval to specify the value in the coronal hole map that indicates a closed-field region (default=0).',
    dest='cfval',
    type=float,
    default=0)

  parser.add_argument('-eps',
    help='Use -eps to specify the tolerance around -cfval (default=1e-5).',
    dest='eps',
    type=float,
    default=1.0e-5)

  parser.add_argument('-t',
    help='Use -t to specify a map for theta, specify this as 2D HDF files (-t requires -p set as well).',
    dest='tfile',
    type=str)

  parser.add_argument('-p',
    help='Use -p to specify a map for phi, specify this as 2D HDF files (-p requires -t set as well).',
    dest='pfile',
    type=str)

  parser.add_argument('-force_ch',
    help='The flag -force_ch forces coronal hole values only.',
    dest='force_ch',
    action='store_true',
    default=False,
    required=False)

  parser.add_argument('-chfile',
    help='The coronal hole map file',
    dest='chfile',
    type=str,
    required=True)

  parser.add_argument('-dfile',
    help='Output file of closest distance to the coronal hole boundary',
    dest='dfile',
    type=str,
    required=True)

  return parser.parse_args()


def ch_distance(args):
  if args.verbose:
    print('=> Reading coronal hole file: '+args.chfile)

  t1, t2, ch_f  = ps.rdhdf_2d(args.chfile)

  # If the data is in pt format, transpose to tp:
  if (np.max(t1) > 3.5):
    t_ch = t2
    p_ch = t1
    ch_f = np.transpose(ch_f)
  else:
    t_ch = t1
    p_ch = t2

  nt_ch = len(t_ch)
  np_ch = len(p_ch)

  if (args.tfile or args.pfile) and not (args.tfile and args.pfile) :
    print('### ERROR in ch_distance.py')
    print('### The options -t and -p must both be set together.')
    exit(1)

  if (args.tfile):
    if (args.verbose):
          print("")
          print('=> Reading theta coordinate file: '+args.tfile)

    t1_t, t2_t, data_t  = ps.rdhdf_2d(args.tfile)

    if (args.verbose):
          print("")
          print('=> Reading phi coordinate file: '+args.pfile)

    t1_p, t2_p, data_p  = ps.rdhdf_2d(args.pfile)

    if len(t1_t) != len(t1_p) or len(t2_t) != len(t2_p):
      print("")
      print('### ERROR in ch_distance.py')
      print('### The theta and phi coordinate files do not have the same dimensions:')
      print('Theta file dimensions: '+ str(len(t1_t))+' '+str(len(t2_t)))
      print('Phi file dimensions: '  + str(len(t1_p))+' '+str(len(t2_p)))
      exit(1)

    # If the data is in pt format, transpose to tp:
    if (np.max(t1_t) > 3.5):
      t_tp = t2_t
      p_tp = t1_t
      data_t = np.transpose(data_t)      
    else:
      t_tp = t1_t
      p_tp = t2_t

    if (np.max(t1_p) > 3.5):
      data_p = np.transpose(data_p)

    nt_tp = len(t_tp)
    np_tp = len(p_tp)

    t = data_t
    p = data_p

  else:

    nt_tp=nt_ch
    np_tp=np_ch

    t_tp=t_ch
    p_tp=p_ch

    one_nt=np.ones(nt_tp)
    one_np=np.ones(np_tp)

    t = np.outer(one_np,t_ch)
    p = np.outer(p_ch,one_nt)

  d_f = np.empty((np_tp,nt_tp))

  if args.verbose:
    print('### Computing the coronal hole distance ...')

  mask = np.empty((np_ch,nt_ch)) 

  in_coronal_hole_list = np.array(abs(ch_f-args.cfval) > args.eps)
  not_coronal_hole_list = np.array(abs(ch_f-args.cfval) <= args.eps)
  
  for j in range(np_ch):
    for i in range(nt_ch):
      if in_coronal_hole_list[j][i]:
        boundary_point = False
        if  (not_coronal_hole_list[max(0,j-1):min(np_tp-1,j+1)+1,max(0,i-1):min(nt_tp-1,i+1)+1]).any():
          boundary_point = True
      else:
        boundary_point = False
        if (in_coronal_hole_list[max(0,j-1):min(np_tp-1,j+1)+1,max(0,i-1):min(nt_tp-1,i+1)+1]).any():
          boundary_point = True

      if boundary_point:
        mask[j][i]=1
      else:
        mask[j][i]=0

  n_ch_boundary_points = int(np.sum(mask))

  if (args.verbose):
    pct=100.0*float(n_ch_boundary_points)/float(nt_ch*np_ch)
    print('### Percentage of points near the coronal hole boundary = '+str(pct)+' %')

  ch_list = np.empty((n_ch_boundary_points))
  x_list = np.empty((n_ch_boundary_points))
  y_list = np.empty((n_ch_boundary_points))
  z_list = np.empty((n_ch_boundary_points))

  k=0
  for j in range(np_ch):
    for i in range(nt_ch):
      if (mask[j][i] != 0):
        ch_list[k]=ch_f[j][i]
        x_list[k],y_list[k],z_list[k] = s2c(1,t_ch[i],p_ch[j])
        k=k+1

  if (args.show_progress):
    print('')

  interp = RegularGridInterpolator((p_ch, t_ch), ch_f, method='nearest')
  x,y,z = s2c(1,t,p)
  one_p=np.ones(nt_tp)
  one_n=-np.ones(nt_tp)

  for j in range(np_tp):
  
    if (args.show_progress):
      print('=> Calculating '+ str(j+1) +' of '+ str(np_tp))

    xdotx0 = np.outer(x_list,x[j][:])+np.outer(y_list,y[j][:])+np.outer(z_list,z[j][:])
    out_coronal_hole_list = abs(ch_list-args.cfval) <= args.eps
    xdotx0_max_out=-1.0e300*one_p
    xdotx0_max_in=-1.0e300*one_p
    for k in range(n_ch_boundary_points):
      if (out_coronal_hole_list[k]):
        xdotx0_max_out = np.maximum(xdotx0[k,:],xdotx0_max_out)
      else:
        xdotx0_max_in = np.maximum(xdotx0[k,:],xdotx0_max_in)

    xdotx0_max_out=np.maximum(xdotx0_max_out,one_n)
    xdotx0_max_out=np.minimum(xdotx0_max_out,one_p)

    xdotx0_max_in=np.maximum(xdotx0_max_in,one_n)
    xdotx0_max_in=np.minimum(xdotx0_max_in,one_p)


    ch_value=interp(np.transpose(np.array((p[j][:],t[j][:]))))

    not_coronal_hole_list = abs(ch_value-args.cfval) <= args.eps

    for i in range(nt_tp):

      if not_coronal_hole_list[i]:
        if (args.force_ch):
          d_f[j][i]=0
        else:
          d_f[j][i]=-np.arccos(xdotx0_max_in[i])
      else:
        d_f[j][i]=np.arccos(xdotx0_max_out[i])

  ps.wrhdf_2d(args.dfile, t_tp, p_tp, d_f)

  if (args.verbose):
    print('=> Wrote the coronal hole distance to file: '+args.dfile)

def in_coronal_hole(value,cfval,eps):
  if (abs(value-cfval) <= eps):
    return False
  else:
    return True

def interp(n,x,xv):
  i = np.searchsorted(x,xv, side='right')-1

  if (n == 1): 
    ip1 = 0
    alpha = 0
  else:
    ip1 = i+1
    if (x[i] == x[ip1]):
      alpha = 0
    else:
      alpha=(xv-x[i])/(x[ip1]-x[i])
  return i,ip1,alpha

def s2c(r,t,p):
  rst=r*np.sin(t)
  x=rst*np.cos(p)
  y=rst*np.sin(p)
  z=r*np.cos(t)
  return x,y,z

def main():
  args = argParsing()
  ch_distance(args)


if __name__ == '__main__':
  main()


