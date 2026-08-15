from __future__ import annotations

import logging
import sys, os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr
from astropy.io import fits
from scipy.ndimage import median_filter, gaussian_filter
from scipy.stats import median_abs_deviation as mad
import matplotlib.pyplot as plt

from core.product import BorgCollective, find_existing_run, next_run_id
from core.registry import update_registry, find_latest_product
from core.instruments import load_instrument_config
from core.html_report import write_registry_html
from core.html_report import _write_table_preview
from core.instrument_utils import get_fits_image_extensions_from_config

logger = logging.getLogger("Spock-1")

# ---------------------------------------------------------------------------
# BAD PIXEL MASKING FUNCTIONS
# ---------------------------------------------------------------------------

def pixel_mask_tight(frame, project, instrument, 
                     mask_showfig=False, mask_savefig=False, mask_deviation=5,
                     bad_output=os.getcwd()):
    """A tighter definition of a bad pixel mask using 5 median absolute devitations from the median, 
    computed column by column (along dispersion direction)"""

    medians = np.median(frame,axis=0)
    mads = mad(frame,axis=0,scale='normal')
    good_pixels = []

    for i,row in enumerate(frame):
        good_pixels.append(((row >= medians-mask_deviation*mads) & (row <= medians+mask_deviation*mads)))

    good_pixels = np.array(good_pixels)
    bad_pixels = ~good_pixels

    percentage_bad_pixels = 100*len(np.where(bad_pixels)[0])/(frame.shape[0]*frame.shape[1])
    print("Percentage of pixels deemed bad by medians and mads = %.2f%%"%percentage_bad_pixels)

    if mask_savefig or mask_showfig:
        plt.figure()
        plt.imshow(bad_pixels)
        plt.title(f"Bad pixel mask using medians and MADS ; deviation {mask_deviation} ; {project} ; {instrument}")

        if mask_savefig:
            plt.savefig(bad_output + '/bad_pixel_mask_medians_MADS_{mask_deviation}.png')
            plt.savefig(bad_output + '/bad_pixel_mask_medians_MADS_{mask_deviation}.pdf')

        if mask_showfig:
            plt.show(block=False)
            plt.pause(5)

        plt.close()

    return bad_pixels

# -----------------------------------

def pixel_mask_loose(frame, project, instrument,
                     mask_showfig=False, mask_savefig=False, mask_deviation=5,
                     bad_output=os.getcwd()):
    """A looser definition of the bad pixel mask using 5 standard deviations from the global mean"""

    good_pixels = ((frame >= np.mean(frame)-mask_deviation*np.std(frame)) & (frame <= np.mean(frame)+mask_deviation*np.std(frame)))
    bad_pixels = ~good_pixels

    percentage_bad_pixels = 100*len(np.where(bad_pixels)[0])/(frame.shape[0]*frame.shape[1])
    print("Percentage of pixels deemed bad by means and stds = %.2f%%"%percentage_bad_pixels)

    if mask_savefig or mask_showfig:

        plt.figure()
        plt.imshow(bad_pixels)
        plt.title(f"Bad pixel mask using means and stds ; deviation {mask_deviation} ; {project} ; {instrument}")

        if mask_savefig:
            plt.savefig(bad_output + '/bad_pixel_mask_means_stds_{mask_deviation}.png')
            plt.savefig(bad_output + '/bad_pixel_mask_means_stds_{mask_deviation}.pdf')

        if mask_showfig:
            plt.show(block=False)
            plt.pause(5)

        plt.close()

    return bad_pixels

# -----------------------------------

def pixel_mask_medfilt(frame, project, instrument, 
                       mask_showfig=False, mask_savefig=False, mask_cutoff=5,
                       bad_output=os.getcwd()):
    """A function that uses median filters along the rows/cross-dispersion direction to locate outliers. 
    Can be more effective."""

    good_pixels = []

    for i,row in enumerate(frame):
        MF = median_filter(row, mask_cutoff)
        residuals = row-MF
        good_pixels.append(((residuals >= -10*mad(residuals,scale='normal')) & (residuals <= 10*mad(residuals,scale='normal'))))

    good_pixels = np.array(good_pixels)
    bad_pixels = ~good_pixels

    percentage_bad_pixels = 100*len(np.where(bad_pixels)[0])/(frame.shape[0]*frame.shape[1])
    print("Percentage of pixels deemed bad by median filter = %.2f%%"%percentage_bad_pixels)

    if mask_savefig or mask_showfig:

        plt.figure()
        plt.imshow(bad_pixels)
        plt.title(f"Bad pixel mask using median filter ; cutoff {mask_cutoff} ; {project} ; {instrument}")
        plt.xlabel('X pixel')
        plt.ylabel('Y pixel')

        if mask_savefig:
            plt.savefig(bad_output + '/bad_pixel_mask_median_filter_{mask_cutoff}.png')
            plt.savefig(bad_output + '/bad_pixel_mask_median_filter_{mask_cutoff}.pdf')

        if mask_showfig:
            plt.show(block=False)
            plt.pause(5)

        plt.close()

    return bad_pixels

# ---------------------------------------------------------------------------
# MAIN CALLABLE FUNCTIONS
# ---------------------------------------------------------------------------

def create_pixel_mask(f, meta, nwin, project, instrument,  mask_savefits, mask_showfig, mask_savefig, mask_cutoff, mask_deviation, bad_pixel_dir, bad_output):

    print('\n')
    print('Testing different pixel masks.')
    # Make bad pixel masks
    if nwin == 1:
        pmt = pixel_mask_tight(f, project, instrument, mask_showfig, mask_savefig, mask_deviation, bad_output)
        pml = pixel_mask_loose(f, project, instrument, mask_showfig, mask_savefig, mask_deviation, bad_output)
        pmmf = pixel_mask_medfilt(f, project, instrument, mask_showfig, mask_savefig, mask_cutoff, bad_output)
    else:
        pmt = np.array([pixel_mask_tight(f[0], project, instrument, mask_showfig, mask_savefig),
                        pixel_mask_tight(f[1], project, instrument, mask_showfig, mask_savefig)])

        pml = np.array([pixel_mask_loose(f[0], project, instrument, mask_showfig, mask_savefig),
                        pixel_mask_loose(f[1], project, instrument, mask_showfig, mask_savefig)])

        pmmf = np.array([pixel_mask_medfilt(f[0], project, instrument, mask_showfig, mask_savefig, mask_cutoff),
                         pixel_mask_medfilt(f[1], project, instrument, mask_showfig, mask_savefig, mask_cutoff)])

    if mask_savefits:
        #pickle.dump(pmt,open("bad_pixel_mask_tight.pickle","wb"))
        save_to_xarray(pmt,
                    bad_pixel_dir,
                    name=f'bad_pixel_mask_medians_MADS_{mask_deviation}',
                    method='tighter definition using 5 std from median',
                    meta=meta)
            
        #pickle.dump(pml,open("bad_pixel_mask_loose.pickle","wb"))
        save_to_xarray(pml,
                    bad_pixel_dir,
                    name=f'bad_pixel_mask_means_stds_{mask_deviation}',
                    method='looser def, 5 std from the global mean',
                    meta=meta)
            
        #pickle.dump(pmmf,open("bad_pixel_mask_medfilt.pickle","wb"))
        save_to_xarray(pmmf,
                    bad_pixel_dir,
                    name=f'bad_pixel_mask_median_filter_{mask_cutoff}',
                    method=f'median filter, {mask_cutoff}',
                    meta=meta,
                    cut_off=mask_cutoff)
        
def run_bad_pixel_masks(
    flat_run_dir,
    nwin,
    sp1_params,
    context,
    storage_format,
    overwrite,
):
    # Get Master Flat
    df = BorgCollective.open_product(flat_run_dir)
    master_flat = df["master_flat"]

    # Test box width
    sigma = sp1_params.get("flat_gaussian_sigma")

    borg = BorgCollective(
        spock_name="Median Smooth",
        spock=1,
        storage_format=storage_format,
    )

    borg.set_parent("spock0", str(flat_run_dir))

    borg.add_parameters({"spock1_flat": {
        "list": sp1_params.get("flat_list"),
        "model": "gaussian",
        "sigma": sigma,
    }})

    borg.set_config_hash_from_parameters()
    borg.set_input_hash_from_parents([flat_run_dir])

    # Output location
    registry_dir = ( flat_run_dir / "models" / "gaussian_smooth" )

    # Find the run with same hashes if existing
    existing = find_existing_run(registry_dir, borg.meta.product_id.config_hash, borg.meta.product_id.input_hash)
    if existing and not overwrite:
        logger.info(f"Skipped: Gaussian_Smooth already exists -> {existing}", extra={"data_name", "flats"})
        return registry_dir / existing
    elif existing and overwrite:
        run_id = existing
    else: 
        run_id = next_run_id(registry_dir) 
    borg.meta.parameters["run_id"] = run_id

    # Running directory
    run_dir = registry_dir / run_id

    master_flat_gaussian_smooth = gaussian_smooth(borg, master_flat, nwin, sigma)

    borg.publish(run_dir)

    update_registry(registry_dir)

    hdu = fits.PrimaryHDU(master_flat_gaussian_smooth)
    hdu.writeto(run_dir / 'master_flat_gaussian_smooth.fits', overwrite=True)
    
    # Update the registry html file
    subtitle=f"Instrument: {context.get('instrument_id')} | Planet: {context.get('project_name')} | Date: {context.get('project_date')}"
    write_registry_html(registry_dir, spock=1, registry_parquet="_registry.parquet", out_html="_registry.html", title="Tiberius-Spock1-Flats-GaussianSmooth", subtitle=subtitle)
   
    logger.info(f"New Gaussian Smooth: {run_id}", extra={"data_name": "flats"})
    
    return run_dir

