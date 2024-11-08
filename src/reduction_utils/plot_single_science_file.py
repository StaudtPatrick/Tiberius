import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import argparse

# Prevent matplotlib plotting frames upside down
plt.rcParams['image.origin'] = 'lower'

parser = argparse.ArgumentParser()
parser.add_argument('fitsfile', help="""Enter the fits file that should be plotted""")
parser.add_argument('-i','--intrinsic', help="""Argument if you want to plot with a better scaling for examining intrinsic CCD problems""",action='store_true')
args = parser.parse_args()

image_file = args.fitsfile
fits.info(image_file)

header = fits.getheader(image_file, ext=0)
#print(header)

image_data = fits.getdata(image_file, ext=0)

plt.figure(figsize=(11,7))
plt.imshow(image_data, cmap='gray')
#plt.title(args.fitsfile, size=16)
plt.xlabel('X pixel', size=16)
plt.ylabel('Y pixel', size=16)
plt.colorbar()
plt.savefig(args.fitsfile.replace(".", "_")[:-5])
plt.show()

if args.intrinsic:
    plt.figure(figsize=(7,7))
    vmin,vmax = np.nanpercentile(image_data,[10,90])
    plt.imshow(image_data,vmin=vmin,vmax=vmax,aspect="auto")
    #plt.title(args.fitsfile, size=16)
    plt.xlabel('X pixel', size=16)
    plt.ylabel('Y pixel', size=16)
    plt.tight_layout()
    plt.savefig(args.fitsfile.replace(".", "_")[:-5] + '_intrinsic_search')
    plt.show()
