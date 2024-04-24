#### Author of this code: James Kirk
#### Contact: jameskirk@live.co.uk

import matplotlib.pyplot as plt
from astropy.io import fits
import numpy as np
import argparse
import sys
import os 
import glob
from PIL import Image
from pathlib import Path

# Prevent matplotlib plotting frames upside down
plt.rcParams['image.origin'] = 'lower'

parser = argparse.ArgumentParser()
parser.add_argument('biaslist', help="""Enter list of bias file names, created through ls > bias.lis in the command line""")
parser.add_argument('-v','--verbose',help="""Display the image of each bias frame before combining it.""",action='store_true')
parser.add_argument('-inst','--instrument',help="""MUST define which instrument we're using, either ACAM or EFOSC""")
parser.add_argument('-c','--clobber',help="""Need this argument to save resulting fits file, default = False""",action='store_true')
parser.add_argument('-e','--eyeball',help="""Use this argument to specify whether bias frames are to be eyeballed - sorting into good and bad frames.""",action='store_true')
parser.add_argument('-s','--savefig',help="""Use this argument to save the bias fits to an gif, default=False""",action='store_true')
args = parser.parse_args()

if args.savefig==True and args.verbose==False:
    print('Attention: You must put verbose=True to store the files!')
    sys.exit(1)

if args.clobber==False and os.path.exists("bias/master_bias.fits"):
    print("Attention: The master_bias.fits file will not be updated. Redo the task with clobber!")

if args.instrument != 'EFOSC' and args.instrument != 'ACAM':
    raise NameError('Currently only set up to deal with ACAM or EFOSC data')


# Find how many windows we're dealing with
if args.instrument == 'EFOSC':
    nwin = 1

if args.instrument == 'ACAM':
    test_file = np.loadtxt(args.biaslist,str)[0]
    test = fits.open(test_file)
    nwin = len(test) - 1

# Creates new subdirectory for saving outputs
Path('./bias').mkdir(parents=True, exist_ok=True)

bias_files = np.loadtxt(args.biaslist,str)

frame_counter = 1

def combine_biases_1window(bias_list,instrument,verbose=False,eyeball=False,savefig=False):
    """median combine biases which were taken with a single window"""
    global frame_counter

    bias_data = []

    if verbose or eyeball:
        plt.figure(figsize=(11,7))

    if eyeball:
        good_frames = []
        bad_frames = []

    for n,f in enumerate(bias_files):

        i = fits.open(f)

        if instrument == 'ACAM':
            data_frame = i[1].data
        if instrument == 'EFOSC':
            data_frame = i[0].data

        print('File #%d/%d ; %s ; Mean = %.1f ; Variance = %.1f ; var/mean = %.2f'%(n+1,len(bias_files),f[-18:-5],np.mean(data_frame),np.var(data_frame),np.var(data_frame)/np.mean(data_frame)))

        bias_data.append(data_frame)

        if verbose or eyeball:
            plt.title('#%d/%d ; %s'%(n+1,len(bias_files),f[-18:-5]))
            plt.imshow(data_frame,vmin=np.median(data_frame)*0.99,vmax=np.median(data_frame)*1.01)
            plt.xlabel("X pixel")
            plt.ylabel("Y pixel")
            plt.colorbar()
            if not eyeball and savefig:
                plt.savefig('bias/' + '%s'%(f[-34:-5]) + '.png')
                frame_counter += 1

            plt.show(block=False) 

            if eyeball: # plot each frame and have user select what is good and bad. NEEDS IMPLEMENTING FOR 2 WINDOWS.
                plt.pause(0.5)
                plt.clf()
                while True:

                    frame_quality = input("good/bad? [g/b]: ")
                    if frame_quality == 'g':
                        good_frames.append(f)
                        if savefig:
                            plt.savefig('bias/' + '%s'%(f[-34:-5]) + '.png')
                        break
                    if frame_quality == 'b':
                        bad_frames.append(f)
                        break

                    print("you have made an invalid choice, try again.")

            else:
                plt.pause(1.0)
                plt.clf()                
            
        i.close()

    if eyeball:
        good_list = open(bias_list+'_GOOD','w')
        bad_list = open(bias_list+'_BAD','w')

        for g in good_frames:
            good_list.write("%s \n"%(g))

        for b in bad_frames:
            bad_list.write("%s \n"%(b))

        good_list.close()
        bad_list.close()

        raise SystemExit()

    bias_data = np.array(bias_data)

    median_combine = np.median(bias_data,axis=0)

    return median_combine




def combine_biases_2windows(bias_list,verbose=False):
    """median combine biases which were taken with two windows"""

    bias_data = [[],[]]

    if verbose:
        plt.figure()


    for n,f in enumerate(bias_files):

        i = fits.open(f)

        for level in range(1,3):

            data_frame = i[level].data

            bias_data[level-1].append(data_frame)

            if verbose:
                plt.subplot(1,2,level)
                plt.title('#%d/%d ; %s'%(n,len(bias_files)-1,f[-12:]))
                plt.imshow(data_frame,vmin=np.median(data_frame)*0.99,vmax=np.median(data_frame)*1.01)
                plt.colorbar()
                if level == 1:
                    plt.xlabel("X pixel")
                    plt.ylabel("Y pixel")
                else:
                    plt.yticks(visible=False)

            print('File = %s ; Mean (window %d) = %f ; Shape (window %d) = %s'%(f,level,np.mean(data_frame),level,(np.shape(data_frame))))

        if verbose:
            plt.show(block=False)
            plt.pause(0.5)
            #plt.close()
            plt.clf()

        i.close()

    bias_data = np.array(bias_data)

    median_combine = np.array([np.median(bias_data[0],axis=0),np.median(bias_data[1],axis=0)])

    return median_combine

def save_fits(data,filename):
    hdu = fits.PrimaryHDU(data)
    hdu.writeto(filename,overwrite=True)
    return

if nwin == 1:
    master_bias = combine_biases_1window(args.biaslist,args.instrument,args.verbose,args.eyeball,args.savefig)
    if args.savefig:
        # Create a GIF using Pillow
        image_files = sorted(glob.glob('bias/EFOSC*.png'))
        images = [Image.open(image_file) for image_file in image_files]

        # Specify the output file path
        output_gif_path = 'bias/bias_movie.gif'

        # Save as a GIF
        images[0].save(output_gif_path, save_all=True, append_images=images[1:], duration=500, loop=0)

        #delete the simple files
        all_files = os.listdir("bias")
        for file in all_files:
            if file.startswith("EFOSC"):
                os.remove(os.path.join("bias",file))

else:
    master_bias = combine_biases_2windows(args.biaslist,args.verbose)

if args.verbose:
    plt.close()

if args.clobber:
    save_fits(master_bias,'bias/master_bias.fits')

## Plot master bias
plt.figure(figsize=(11,7))
plt.title('Master Bias', size=16)
if nwin == 1:
     plt.imshow(master_bias,vmin=np.median(master_bias)*0.99,vmax=np.median(master_bias)*1.01)
     plt.ylabel("Y pixel")
     plt.xlabel("X pixel")
else:
     plt.subplot(121)
     plt.imshow(master_bias[0],vmin=np.median(master_bias[0])*0.99,vmax=np.median(master_bias[0])*1.01)
     plt.ylabel("Y pixel")
     plt.xlabel("X pixel")
     plt.subplot(122)
     plt.imshow(master_bias[1],vmin=np.median(master_bias[0])*0.99,vmax=np.median(master_bias[0])*1.01)
     plt.yticks(visible=False)

plt.colorbar()
if args.clobber:
    plt.savefig('bias/master_bias.png')
plt.show()
