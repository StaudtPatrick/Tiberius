#### Author of this code: James Kirk
#### Contact: jameskirk@live.co.uk

import matplotlib.pyplot as plt
from astropy.io import fits
import numpy as np
import argparse
from scipy.ndimage import median_filter
import pickle
import os
import copy
from PIL import Image
import re
import glob

# Prevent matplotlib plotting frames upside down
plt.rcParams['image.origin'] = 'lower'

parser = argparse.ArgumentParser()
parser.add_argument('sciencelist', help="""Enter list of science .fits file names""")
parser.add_argument('-b','--bias_frame',help="""Define the bias frame. Not essential, can be run without a bias frame.""")
parser.add_argument('-mask','--bad_pixel_mask',help="""Optionally parse in a bad pixel mask to ignore these pixels from the cosmic flagging""")
parser.add_argument('-row','--rows',help="""Optionally define the row location of n test pixels before executing all rows""",type=int,nargs="+")
parser.add_argument('-col','--cols',help="""Optionally define the column location of n test pixels before executing all columns""",type=int,nargs="+")
parser.add_argument('-pixel_clip','--pixel_clip',help="""Define the outlier rejection threshold/sigma clip. Default = 5""",type=float,default=5.)
parser.add_argument('-frame_clip','--frame_clip',help="""Define the multiplicative factor at which a frame's rejection detection is deemed to have failed. Default = 3, i.e. if a frame has 3x the median number of cosmics, it's deemed to potentially have failed.""",type=float,default=3.)
parser.add_argument('-v','--verbose',help="""Display all cosmic pixel masks. Display all pixel signals to a max number of cosmic signals (default 20) """,action='store_true')
parser.add_argument('-save_cosmics','--save_cosmics', help="""Save the amount of cosmic signals from verbose (default 20)""", action='store_true')
parser.add_argument('-save_frames','--save_frames',help="""Save cosmic pixel plots""",action='store_true')
parser.add_argument('-jwst','--jwst',help="""Use this option if we're looking at JWST data as the input fits files have a different format""",action='store_true')
args = parser.parse_args()

plot_counter = 0
max_plots = 20

if args.save_cosmics and not args.verbose:
    print('Attention: Cosmic plots can only be saved if you also display all cosmic pixel masks. Redo the task with -v argument!')

# load in the list of science file names
science_list = np.atleast_1d(np.loadtxt(args.sciencelist,dtype=str))

# optionally load in the master bias
if args.bias_frame is not None:
    master_bias = fits.open(args.bias_frame)[0].data
    bias = True
else:
    bias = False


# load in the science data
print("Loading in data...")
data = []
nints = []

for s in science_list:
    f = fits.open(s,memmap=False)
    if args.jwst:
        data.append(f["SCI"].data)
        nints.append(f["SCI"].data.shape[0])
    else:
        if bias: # subtract the bias if using one
            data.append(f[0].data-master_bias)
        else:
            data.append(f[0].data)
        nints.append(f[0].data.shape[0])
    f.close()

nints = np.cumsum(nints)

if args.jwst:
    data = np.vstack(data)
else:
    data = np.array(data)
    
if args.bad_pixel_mask is not None:
	mask = pickle.load(open(args.bad_pixel_mask,"rb"))
	data[:,mask] = np.nan

if args.save_cosmics or args.save_frames:
    try:
        os.mkdir("locate_cosmics")
    except:
        pass

# define the cosmic pixel flagged array, initially as an array of zeros matching the dimensions of the input data
cosmic_pixels = np.zeros_like(data)
nframes,nrows,ncols = data.shape

# define the sigma cut off
cut_off = args.pixel_clip

def locate_bad_frames(image_data,pixel_row,pixel_col,cut_off,verbose=False,save_cosmics=False):
    """The function that locates the frames/pixels where cosmics are located.

    Inputs:
    image_data - the image data, dimensions of nframes x nrows x ncols
    pixel_row - the row number of the pixel under consideration
    pixel_col - the column number of the pixel under consideration
    cut_off - the sigma cut off / outlier rejection threshold
    verbose - True/False - plot the outlier identififcation for this pixel?

    Returns:
    bad_frames - the array of frames for which this pixel is an outlier"""
    
    global plot_counter

    nframes,nrows,ncols = image_data.shape
    pixel = image_data[:,pixel_row,pixel_col].astype(float) # make sure that the science data is correctly defined as floats
    median = median_filter(pixel,3) # take a running median across 3 frames for each pixel

    # deal with edge effects of the running median
    median[0] = np.median((median[0],median[1]))
    median[-1] = np.median((median[-1],median[-2]))

    residuals = pixel - median # calulate residuals
    good_frames = ((residuals <= cut_off*np.nanstd(residuals)) & (residuals >= -cut_off*np.nanstd(residuals))) # locate the good frames based on residuals array

    bad_frames = ~good_frames # flip the sign to find the outliers
    
    # ignore the nans (saturated pixels)
    bad_frames[~np.isfinite(residuals)] = False

    if verbose and plot_counter < max_plots: # plot output
        plt.figure(figsize=(11,7))
        plt.subplot(211)
        plt.plot(pixel,label="Pixel value")
        plt.plot(median,label="Running median")
        plt.title("Pixel [%d,%d]"%(pixel_row,pixel_col))
        plt.ylabel("Counts (ADU)")
        plt.plot(np.arange(nframes)[bad_frames],pixel[bad_frames],"rx",label="Flagged outliers")
        plt.legend()

        plt.subplot(212)
        plt.ylabel("Residuals")
        plt.xlabel("Frame")
        plt.plot(residuals)
        plt.axhline(cut_off*np.nanstd(residuals),ls='--',color='k')
        plt.axhline(cut_off*-np.nanstd(residuals),ls='--',color='k',label="cut-off")
        plt.plot(np.arange(nframes)[bad_frames],residuals[bad_frames],"rx",label="Flagged outliers")
        plt.legend()

        if any(bad_frames):
            plot_counter +=1
            if save_cosmics :
                try:
                    os.mkdir("locate_cosmics/single_cosmics")
                except:
                    pass
                plt.savefig('locate_cosmics/single_cosmics/pixel_over_time_' + str(plot_counter) +'.png') 

        plt.show(block=False)
        plt.pause(1e-6)
        plt.clf()
        plt.close()

    return bad_frames,median


def plot_cosmic_frames(cosmic_pixels, save_frames=False):
    """A function that plots all cosmics frames"""
    plt.figure(figsize=(11,7))
    for i,c in enumerate(cosmic_pixels):
        plt.imshow(c,cmap='Greys', interpolation='none',aspect="auto")
        plt.title("Frame %d"%(i+1))
        plt.xlabel("Pixel column")
        plt.ylabel("Pixel row")
        if save_frames:
            filename = "Frame_%d"%(i+1)
            plt.savefig('locate_cosmics/' + filename + '.png')
        plt.show(block=False)
        plt.pause(1e-6)
        plt.clf()
    return

def check_cosmic_frames(cosmic_pixels,frame_cut_off,save_frames=False):
    """A function that plots and optionally resets cosmic pixels for frames where a disproportionate number of pixels have been flagged as cosmics.

    Inputs:
    cosmic_pixels - the array of all cosmic flagged pixels, dimensions of nframes x nrows x ncols

    Returns:
    cosmic_pixels - the new array of all cosmic flagged pixels, taking into the account the user-defined reset frame masks"""

    nframes,nrows,ncols = cosmic_pixels.shape

    ncosmics = []

    for i,c in enumerate(cosmic_pixels):
        ncosmics.append(len(np.where(c)[0]))

    median_cosmics = np.nanmedian(ncosmics)
    if median_cosmics == 0:
        median_cosmics = 1

    print("Median number of cosmics per frame = %d (%.3f%%)"%(median_cosmics,100*median_cosmics/(nrows*ncols)))

    incorrectly_flagged_cosmics = []

    for i,c in enumerate(cosmic_pixels):
        ncosmics = len(np.where(c==1)[0])
        if ncosmics > frame_cut_off*median_cosmics:
            print("Integration %d has %.2fX the median number of cosmics, somethings up"%(i+1,ncosmics/median_cosmics))
            plt.figure(figsize=(11,7))
            plt.imshow(c,cmap='Greys', interpolation='none',aspect="auto")
            incorrectly_flagged_cosmics.append(i)
            plt.title("Integration %d"%(i+1))
            plt.ylabel("Pixel row")
            plt.xlabel("Pixel column")
            plt.show(block=False)
            #plt.clf()
            plt.close()
            
            reset_mask = input("Reset mask for integration %d? [y/n]: "%(i+1))
            if reset_mask == "y":
                print("...resetting mask\n")
                cosmic_pixels[i] = np.zeros_like(c)
                if save_frames:
                    plt.figure(figsize=(11,7))
                    plt.imshow(cosmic_pixels[i],cmap='Greys', interpolation='none', aspect="auto")
                    plt.title("Integration %d"%(i+1))
                    plt.ylabel("Pixel row")
                    plt.xlabel("Pixel column")
                    plt.savefig('locate_cosmics/Frame_%d'%(i+1))
                    plt.show()
                    plt.close()

    return cosmic_pixels


def replace_cosmics(cosmic_pixels,medians,science_list,nints,jwst=False):

    try:
        os.mkdir("../science_files_cosmic_cleaned")
    except:
        pass

    nframes,nrows,ncols = cosmic_pixels.shape
    total_nints = nints[-1]

    if jwst:

        for i,c in enumerate(cosmic_pixels):

            jwst_fits_counter = np.digitize(i,nints)
            if i == 0 or i in nints:
                fits_file = fits.open(science_list[jwst_fits_counter],memmap=False)
                new_fits_file = copy.deepcopy(fits_file)
                filename = science_list[jwst_fits_counter].split("/")[-1]

            if jwst_fits_counter > 0:
                jwst_index_counter = i-nints[jwst_fits_counter]
            else:
                jwst_index_counter = i

            print("Cleaning integration %d, %s"%(i,filename))

            for row in range(nrows):
                new_fits_file["SCI"].data[jwst_index_counter][row][c[row]] = medians[i][row][c[row]]

            if i in nints-1:
                fits_file.close()
                print("Saving cosmic_cleaned_fits/%s"%(filename))
                new_fits_file.writeto("../science_files_cosmic_cleaned/%s"%filename,overwrite=True)

        return



        # fits_files = [fits.open(s,memmap=False) for s in science_list]
        # new_fits_files = [copy.deepcopy(f) for f in fits_files]
        # filenames = [s.split("/")[-1] for s in science_list]
        # nints = np.cumsum([f["SCI"].data.shape[0] for f in fits_files])
        # total_nints = nints[-1]

        for s in science_list:
            fits_file = fits.open(s,memmap=False)
            new_fits_file = copy.deepcopy(fits_file)
            filename = s.split("/")[-1]

            for i,c in enumerate(cosmic_pixels):

                jwst_fits_counter = np.digitize(i,nints)

                if jwst_fits_counter > 0:
                    jwst_index_counter = i-nints[jwst_fits_counter]
                else:
                    jwst_index_counter = i

                print("Cleaning integration %d, %s"%(i,filenames[jwst_fits_counter]))

                for row in range(nrows):
                    new_fits_files[jwst_fits_counter]["SCI"].data[jwst_index_counter][row][c[row]] = medians[i][row][c[row]]

            for i,nf in enumerate(new_fits_files):
                print("Saving cosmic_cleaned_fits/%s"%(filenames[i]))
                nf.writeto("cosmic_cleaned_fits/%s"%filenames[i],overwrite=True)

        return



    for i in range(nframes):
        f = fits.open(science_list[i])
        f_new = copy.deepcopy(f)
        filename = science_list[i].split("/")[-1]

        print("Cleaning frame %i"%(i+1))

        for row in range(nrows):
            f_new[0].data[row][cosmic_pixels[i][row]] = medians[i][row][cosmic_pixels[i][row]]

        f_new.writeto("../science_files_cosmic_cleaned/%s"%filename,overwrite=True)
        f.close()

    return




## If using the verbose option for the median filter, I'm assuming this is a test so I don't run the full script
if args.rows is not None:
    for r,c in zip(args.rows,args.cols):
        locate_bad_frames(data,r,c,cut_off,args.verbose,args.save_cosmics)
    raise SystemExit

# loop through all frames and pixels
cosmic_pixels = np.zeros_like(data)
median_values = np.zeros_like(data)

for row in range(nrows):
    print("Calculating medians for row %d of %d"%(row+1,nrows))
    for col in range(ncols):
        bad_frames,medians = locate_bad_frames(data,row,col,cut_off,args.verbose,args.save_frames)
        cosmic_pixels[:,row,col][bad_frames] = 1
        median_values[:,row,col] = medians

cosmic_pixels = cosmic_pixels.astype(bool)

def extract_frame_number(file_path):
    # Extract the frame number from the file path
    match = re.search(r'\d+', file_path)
    return int(match.group()) if match else -1

# check the output
if args.verbose:
    print("\nPlotting all cosmic-masked pixels...\n")
    plot_cosmic_frames(cosmic_pixels, args.save_frames)
    
    if args.save_frames:
        image_files = sorted(glob.glob('locate_cosmics/Frame_*.png'), key=extract_frame_number)
        images = [Image.open(image_file) for image_file in image_files]

        # Specify the output file path
        output_gif_path = 'locate_cosmics/cosmics_movie.gif'

        # Save as a GIF
        images[0].save(output_gif_path, save_all=True, append_images=images[1:], duration=1000, loop=0)

# double-check the output
if not args.verbose:
    print("Plotting frames with high number of cosmics...\n")
    cosmic_pixels = check_cosmic_frames(cosmic_pixels, args.frame_clip, args.save_frames)
    if args.save_frames:
        image_files = sorted(glob.glob('locate_cosmics/Frame_*.png'), key=extract_frame_number)

        if len(image_files) >= 2:
            images = [Image.open(image_file) for image_file in image_files]

            # Specify the output file path
            output_gif_path = 'locate_cosmics/cosmics_corr_movie.gif'

            # Save as a GIF
            images[0].save(output_gif_path, save_all=True, append_images=images[1:], duration=500, loop=0)
        else:
            pass
            

# save the cosmic masks
pickle.dump(cosmic_pixels,open("locate_cosmics/cosmic_pixel_mask_%dsigma_clip.pickle"%(cut_off*10),"wb"))

# optionally save new fits files with cosmics replaced by median pixel values
# note: this doesn't offer much improvement over the interpolation performed in long_slit_science_extraction.py

replace = input("Replace cosmic values with median and save to new fits? [y/n]: ")
if replace == "y":
    replace_cosmics(cosmic_pixels,median_values,science_list,nints,args.jwst)
