#!/usr/bin/env python3
import os
import argparse
import string
import numpy as np

import psihdf as ps

def get_prefix(s):
    # Define what characters are considered letters
    letters = set(string.ascii_letters)
    # Iterate through each character in the string
    for i, char in enumerate(s):
        if char not in letters:
            # Return the substring from the start to the current index
            return s[:i]
    # If no non-letter character is found, return the whole string
    return s


def main():
    parser = argparse.ArgumentParser(description="Convert pt h5 files from SWiG into tp h5 files in mas units for use with heliospheric simulations.")
    parser.add_argument("input_dir", help="Path to the input directory containing SWiG files")
    parser.add_argument("output_dir", help="Path to the output directory")
    args = parser.parse_args()

    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Mapping prefixes to flags
    prefix_units = {
        't': 2.807066716734894e7,
        'vr': 481.371067364613509,
        'vt': 481.371067364613509,
        'vp': 481.371067364613509,
        'rho': 1.672600000000000e-16,
        'br': 2.206891397800740,
        'bt': 2.206891397800740,
        'bp': 2.206891397800740
    }

    # Process each .h5 file in the input directory
    for filename in os.listdir(args.input_dir):
        if filename.endswith('.h5'):
            filepath = os.path.join(args.input_dir, filename)
            prefix = get_prefix (filename)

            if prefix in prefix_units:
                print("Processing "+filename+"...")
                unit_fac = prefix_units[prefix]
                [x,y,data] = ps.rdhdf_2d(os.path.join(args.input_dir, filename))
                data = np.transpose(data)/unit_fac

# ADD ZERO TRANSVERSE COMPONENTS HERE?  LINK TO FIRST ONE?
# ADD PROPER REMESH GENERAL?  WHAT GRIDS?


                output_file = os.path.join(args.output_dir, filename)                
                ps.wrhdf_2d(output_file,y,x,data)


if __name__ == "__main__":
    main()
