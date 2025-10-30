.. _EFOSC2:

Handling EFOSC2 Data
====================
Firstly, you will need to download your data! Navigate to the `ESO <https://archive.eso.org/eso/eso_archive_main.html>`_ science archive facility and find your target. Check the box of the files you want to acquire and download the files.

Stage 1: File and Folder Structure
------------------------------------

.. _stage1:
Under your project folder build the following three folders: ``raw_science_files``, ``calib_files`` and ``data_analysis``.
After downloading and unpacking the EFOSC2 data, save the actual spectroscopic science files and calibration files (e.g. bias, flat, arc) into the corresponding folders.

1.1: Working Lists
~~~~~~~~~~~~~~~~~~~~~~~~~~
This part is necessary to build all the lists that are used to access the science files. Run the following command in both folders:

.. code-block:: bash

  $ python -m reduction_utils.EFOSC_utils.sort_EFOSC_files -c

The argument -c enables it to overwrite files.

.. note::

  In case the list names contain blank spaces, change it to ``_``. Then copy the list containing the paths of the single science files to the ``data_analysis`` folder.

1.2: Generate Gifs
~~~~~~~~~~~~~~~~~~~~~~~~~~
For a better understanding of the data, visualize the science frames and the arc files in gifs. Therfor, call in the ``calib_files`` and in the ``science_files_raw`` folders:

.. code-block:: bash
  
  $ python -m reduction_utils.generate_gifs list -inst=instrument -out=outputname -i

list: list for raw files and arc files\\
-inst: instrument; argument for the used instrument (EFOSC2)\\
-out: outputname; argument for the name of the output file\\
-i: intrinsic; argument if you want to have a better scaling


Stage 2: Data Reduction on Raw Science Frame Level
---------------------------------

.. _stage2:

2.1: Bias Correction
~~~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

2.2: Flat Fielding
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

2.3: Cosmic Ray Correction
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

2.4: CCD impurities
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction


Stage 3: Extraction
------------------------------

.. _stage3:
Under construction


Stage 4: Data Reduction on Spectral Level
------------------------------

.. _stage4:

4.1: Cosmic Ray Correction
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

4.2: Arc Calibration
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

4.3: Spectral Resampling
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

4.4: Wavelength Calibration
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

4.5: Wavelength Bins
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction

4.6: White-Light Lightcurve
~~~~~~~~~~~~~~~~~~~~~~~~
Under construction


Stage 5: Fitting
------------------------------

.. _stage5:
Under construction



