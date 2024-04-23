import numpy as np
import os
from astropy.io import fits
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse

parser = argparse.ArgumentParser(description='Make arc movies')
parser.add_argument("arclist", help="Load in the list of arc files")
parser.add_argument("-out", "--output", help="Output file name")
parser.add_argument("-cmap", "--colormap", default='gray', help="Colormap for the output plots")
args = parser.parse_args()


plt.rcParams['image.origin'] = 'lower'

def init(i):
    f = file_list[i]
    print(f, i) 
    frame = fits.open(f)

    # Assuming data is a 2D array representing an image
    im.set_data(frame[0].data)
    ax.set_title(f"{file_list[i][-34:]}")

    frame.close()

    return im,
 
# Import Arc list
file_list = np.loadtxt(args.arclist,str)

# Additional setup for the animation
fig, ax = plt.subplots(figsize=(11,7))

# The number of frames in the animation
nframes = len(file_list)

# Create the initial plot with the first frame data
first_frame = fits.open(file_list[0])
im = ax.imshow(first_frame[0].data, cmap=args.colormap)
first_frame.close()

# Create animation
anim = animation.FuncAnimation(fig, init, frames=nframes, repeat=False, save_count=0)

# Save the animation as a GIF
output_gif = args.output
output_gif = output_gif + ".gif"
anim.save(output_gif, writer='imagemagick', fps=1)

print(f'GIF created successfully: {output_gif}')
