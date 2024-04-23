import numpy as np
import matplotlib.pyplot as plt
import copy
import argparse
import os
from astropy.io import  fits

def nan_helper(y):
    return np.isnan(y), lambda z: z.nonzero()[0]

def interpolate_row(data, row):
    nans, x = nan_helper(data[row, : ])
    data[row, nans]= np.interp(x(nans),x(~nans),data[row,~nans])

def interpolate_fits_file(input_file, output_file, column_info):
    # Read the .FITS file
    with fits.open(input_file) as hdul:
        # Copy the original file
        header_copy = copy.deepcopy(hdul[0].header)
        # Extract the data from the deepcopy
        data = copy.deepcopy(hdul[0].data.astype(float))

        # Iterate over each specified column and row range
        for col, row_range in column_info:
            # Set values in specified columns and row ranges to NaN
            data[row_range[0]:row_range[1], col] = np.nan

        # Perform interpolation over the entire data matrix
        for i in range(data.shape[0]):
            interpolate_row(data, i)

        # Save the interpolated data to the output file
        new_hdu = fits.PrimaryHDU(data, header=header_copy)
        new_hdul = fits.HDUList([new_hdu])

        new_hdul.writeto(output_file, overwrite=True)


if __name__ == "__main__":

    plt.rcParams['image.origin'] = 'lower'

    parser = argparse.ArgumentParser(description="Interpolate FITS files")

    parser.add_argument('input_file_list', help="Path to the text file including the list of input FITS files")
    parser.add_argument('output_folder', help="Path to the output folder")
    parser.add_argument('-colinfo', '--column_info', help="Path to the input file containing column indices and row ranges, in the form that each line consists of column rowstart rowstop")
    parser.add_argument('-range','--interpolation_range', type=int, help="The range of interpolation to the left and right of each NaN value", default=20)
    args = parser.parse_args()

    with open(args.input_file_list, 'r') as file:
        input_files = [line.strip() for line in file]

    with open(args.column_info, 'r') as file:
        lines = file.readlines()

    column_info = []
    for line in lines:
        col, start, end = map(int, line.strip().split())
        column_info.append((col, (start, end)))
    
    try: 
        os.mkdir(args.output_folder)
    except FileExistsError:
        pass

    for input_file in input_files:
        # Generate the output file path based on the input file name
        output_file = f"{args.output_folder}/{input_file.split('/')[-1]}" 
        
        # Interpolate for the current input file
        print(f'Interpolate {input_file[-34:]}')
        interpolate_fits_file(input_file, output_file, column_info)

