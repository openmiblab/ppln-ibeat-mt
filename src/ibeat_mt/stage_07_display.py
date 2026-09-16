import logging
import os
from pathlib import Path

import numpy as np

from miblab import pipe
import dbdicom as db
from miblab_plot import mosaic_overlay

from utils import data, dicom

from vreg import mod_affine # to be removed once GH PR merged

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline

KIDNEY_MAP = { 1: "kidney_left",
                2: "kidney_right",
                }

SPINE_MAP = {  1: "vertebrae",
                2: "spinal_cord",
            }


def display_all(db_data, db_mosaics, dir_kidneys, dir_spine, contains=None):

    print('Loading moco mean average (base) series')
    # Load moco mean average (base) DICOM series
    base_series = db.series(db_data, contains=contains)

    for series in base_series:

        print(f"Running on series: {series}")

        # Extract participant ID and study & series descriptions
        participant, study, descr = dicom.get_attributes(series)

        base_vol, base_array = dicom.get_vol_arrays(series)

        # get other studies
        kidney_study = data.get_related_study(dir_kidneys, series)
        spine_study = data.get_related_study(dir_spine, series)
        
        if 'K_align' in descr:
            mask_series = kidney_study + [('kidney_masks', 0)]
            class_map = KIDNEY_MAP
        elif 'map' in descr:
            mask_series = spine_study + [('spine_masks', 0)]
            class_map = SPINE_MAP
        else:
            print(f'skipping {participant} - kidney and spine align underlay missing')
            continue

        # Skip if align missing for this dataset
        if data.skip_missing(db_data, participant, study) == True:
            logging.info(f"Series align {participant} missing --- skipping")
            continue

        # Skip if kidney masks missing for this dataset
        if data.skip_missing(dir_kidneys, participant, study) == True:
            logging.info(f"Series kidneys {participant} missing --- skipping")

        # Skip if spine masks missing for this dataset
        if data.skip_missing(dir_spine, participant, study) == True:
            logging.info(f"Series spine {participant} missing --- skipping")
                
        png_file = os.path.join(db_mosaics, f"{participant}_{study}_{mask_series[-1][0]}.png")
                
        # Skip if file exists
        if os.path.exists(png_file):
            continue
                        
        try:
            mask_vol = db.volume(mask_series)
                
            #mask_resliced = mask_vol.slice_like(base_vol).values
            # Call the underlying slice_like directly to pass spline order=0 (nearest-neighbour)
            mask_resliced, resliced_affine = mod_affine.affine_reslice(mask_vol.values, 
                                                                        mask_vol.affine, 
                                                                        base_vol.affine, 
                                                                        output_shape=base_vol.shape,
                                                                        order=0  # bspline order, 0 = nearest-neighbour
                                                                        )

            rois = {roi: (mask_resliced==idx).astype(np.int16) for idx, roi in class_map.items()}

            # Build mosaic and log success
            mosaic_overlay(base_array, rois, png_file, vmin=0, vmax=np.percentile(base_array, 90), margin=[16,16,2], opacity=0.4)
            logging.info(f"Success building mosaic for {participant}, {study}, {mask_series[-1][0]}.")

        except:
            logging.exception(f"Error building mosaic for {participant}, {study}, {mask_series[-1][0]}.")


def run(build, logfile):

    logging.info("Stage 1 --- Create mosaic of mask overlays ---")
    
    # Import external pipelines
    # kidney masks
    kidneyvol_ppln = data.get_external_buildpath(__file__, 'kidneyvol', 'stage_3_edit')

    # spine masks
    spine_ppln = data.get_external_buildpath(__file__, 'totspineseg', 'stage_01_auto_segment')

    # data from root folder (same pipeline)
    for site in ['Leeds', 'Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:

        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='06_align')
        patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients')

        dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Patients', site)
        dir_spine = os.path.join(spine_ppln, 'Patients', site)

        dir_map = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='05_map')
        
        print(f'Running display kidneys: {site} patients')
        display_all(patients_input, patients_output, dir_kidneyvol, dir_spine, contains='atr')

        print(f'Running display spine: {site} patients')
        display_all(dir_map, patients_output, dir_kidneyvol, dir_spine, contains='AVR')
      
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='06_align')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')

    dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Controls')
    dir_spine = os.path.join(spine_ppln, 'Controls')
    
    dir_map = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='05_map')

    print(f'Running display kidneys: controls')
    display_all(controls_input, controls_output, dir_kidneyvol, dir_spine, contains='atr')
    
    print(f'Running display spine: {site} patients')
    display_all(dir_map, controls_output, dir_kidneyvol, dir_spine, contains='AVR')


if __name__=='__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage display
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
