import logging
import os
from pathlib import Path

import numpy as np

from miblab import pipe
import dbdicom as db
import pydmr
import numpyradiomics as npr

from utils import data, dicom

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline

KIDNEY_MAP = {1: "kidney_left",
            2: "kidney_right",
            }

SPINE_MAP = { # 1: "vertebrae",
                2: "spinal_cord",
            }


def get_binaries(mask_array, mask_label):

  binary_mask = (mask_array == mask_label).astype(np.float32)
  
  if np.sum(binary_mask) == 0:
    logging.error(f"{mask_label} - Error: binary mask is equal to zero")
    return
  else:
    return binary_mask


def align_masks(mask_series, map_vol, idx):
    
    mask_vol = db.volume(mask_series)
    mask_resliced = mask_vol.slice_like(map_vol)

    # Read binary mask
    binary_mask = get_binaries(mask_resliced.values, idx)

    return binary_mask


def combine(dir_output, pipeline, convert=False):
    """
    Concatenate all dmri files in a folder into a single dmr file. 
    Create long and wide format csvs for export.
    """

    # Combine all dmr files into one
    folder = Path(dir_output)
    dmr_files = list(folder.rglob("*.dmr.zip"))

    if dmr_files != []:
        dmr_files = [str(f) for f in dmr_files]

        dmr_file = os.path.join(dir_output, f'{pipeline}_all_masks')

        dmr_concat = pydmr.concat(dmr_files, dmr_file, cleanup=True)

        if convert==True:
            pydmr.pars_to_long(dmr_concat, os.path.join(dir_output, f'{pipeline}_all_masks_long.csv'))
            pydmr.pars_to_wide(dmr_concat, os.path.join(dir_output, f'{pipeline}_all_masks_wide.csv'))


def calculate_stats(map_vol, binary_mask, roi, participant, study, dmr_file):
    
    # Get radiomics shape features in cm
    results = npr.firstorder(map_vol.values, binary_mask, extend=True)
    units = npr.firstorder_units('%', 'mm')

    # Write to dmr file
    dmr = {
        'data': {f"{roi}-MTR-firstorder-{p}": [f"First order measure {p} for {roi}", u, 'float'] for p, u in units.items()},
        'pars': {(participant, study, f"{roi}-MTR-firstorder-{p}"): v for p, v in results.items()}
        }

    pydmr.write(dmr_file, dmr)
    logging.info(f"Successfully computed shapes: {roi}")


def measure_mask(kidney_series, spine_series, map_vol, MTR_vol, dir_output):

    for mask_series in [kidney_series, spine_series]:

        participant, study, descr = dicom.get_attributes(mask_series)
        manufacturer = db.values(mask_series, 'Manufacturer')[0]

        if 'kidney' in mask_series[-1][0]:
            class_map = KIDNEY_MAP
            base_vol = map_vol
        if 'spine' in mask_series[-1][0]:
            class_map = SPINE_MAP
            base_vol = MTR_vol

        for idx, roi in class_map.items():
            
            # Define outputs
            fname = f"{participant}_{study}_{roi}.dmr.zip"
            dmr_file = os.path.join(dir_output, fname)

            # Skip if output exists
            if os.path.exists(dmr_file):
                continue

            try:
                binary_mask = align_masks(mask_series, base_vol, idx)
                calculate_stats(base_vol, binary_mask, roi, participant, study, dmr_file)
            except:
                logging.exception(f"Error computing shapes: {fname}")


def measure_all(dir_map, dir_output, dir_kidneys, dir_spine, dir_MTR, pipeline, contains=None, site = None):

    print('Loading MTR map series')
    # Load MTR map DICOM series
    map_series = db.series(dir_map, contains = contains)

    for series in map_series:

        print(f"Running on series: {series}")

        # Extract participant ID and study & series descriptions
        participant, study, descr = dicom.get_attributes(series)

        # Check if measure already exists for this dataset
        if data.skip_existing(dir_output, participant, study) == True:
            logging.info(f"Series {participant} already exists --- skipping")
            continue

        map_vol = db.volume(series)

        kidney_study = data.get_related_study(dir_kidneys, series)
        spine_study = data.get_related_study(dir_spine, series)
        mt_study = data.get_related_study(dir_MTR, series)
        mt_series = db.series(mt_study, contains='MTR')
        MTR_vol = db.volume(mt_series[0])

        kidney_series = kidney_study + [('kidney_masks', 0)]
        spine_series = spine_study + [('spine_masks', 0)]

        # Skip if kidney masks missing for this dataset
        if data.skip_missing(dir_kidneys, participant, study) == True:
            logging.info(f"Series kidneys {participant} missing --- skipping")
            continue

        # Skip if spine masks missing for this dataset
        if data.skip_missing(dir_spine, participant, study) == True:
            logging.info(f"Series spine {participant} missing --- skipping")
            continue

        measure_mask(kidney_series, spine_series, map_vol, MTR_vol, dir_output)
    
    if site == None:
        combine(dir_output, f"Controls_{pipeline}", convert=True)
    else:
        combine(dir_output, f"{pipeline}_{site}")


def run(build, logfile):

    logging.info("Stage 1 --- Measuring MTR ---")

    # Import external pipelines
    # kidney masks
    kidneyvol_ppln = data.get_external_buildpath(__file__, 'kidneyvol', 'stage_3_edit')

    # spine masks
    spine_ppln = data.get_external_buildpath(__file__, 'totspineseg', 'stage_01_auto_segment')

    patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients')

    # data from root folder (same pipeline)
    for site in ['Leeds', 'Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:

        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='06_align')

        dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Patients', site)
        dir_spine = os.path.join(spine_ppln, 'Patients', site)

        dir_MTR = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='05_map')
        
        print(f'Measuring: {site} patients')
        measure_all(patients_input, patients_output, dir_kidneyvol, dir_spine, dir_MTR, PIPELINE, contains='mtr', site = site)
    
    combine(patients_output, f"Patients_mt", convert=True)
      
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='06_align')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')

    dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Controls')
    dir_spine = os.path.join(spine_ppln, 'Controls')
    
    dir_MTR = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='05_map')

    print(f'Measuring: controls')
    measure_all(controls_input, controls_output, dir_kidneyvol, dir_spine, dir_MTR, PIPELINE, contains='mtr')


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage measure
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
