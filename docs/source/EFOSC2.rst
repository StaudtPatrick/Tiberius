.. _EFOSC2:

Handling EFOSC2 DATA
====================
Firstly, you will need to download your data! Navigate to the `ESO <https://archive.eso.org/eso/eso_archive_main.html>`_ science archive facility and find your target. Check the box of the files you want to aquire and download the files.

Stage 1: File and Folder Structure
------------------------------------

.. _stage1:

After downloading and unpacking the EFOSC2 data, save the actual spectroscopic science files into the folder ``raw_science_files`` and the calibration files (e.g. bias, flat, arc, ...) into the ``calib_folder``.
Then build the folder ``data_analysis``.

1.1: Working Lists
~~~~~~~~~~~~~~~~~~~~~~~~~~
This part is necessary to build all the lists that are used to access the science files. Run the following command in both folders:

.. code-block:: bash

  $ python -m reduction_utils.EFOSC_utils.sort_EFOSC_files -c

The argument -c enables it to overwrite files.

.. note::

  In case the list names contain blanck spaces, change it to ``_``. Then copy the list containing the paths of the single science files to the ``data_analysis`` folder.


Stage 2: DATA REDUCTION ON RAW SCIENCE FRAME LEVEL
---------------------------------

.. _stage2:

2.1: Bias Correction
~~~~~~~~~~~~~~~~~~~~~~~~~~
Test 

2.2: Flat Fielding
~~~~~~~~~~~~~~~~~~~~~~~~
Test


Stage 3: FITTING
------------------------------

.. _stage3:
Test



