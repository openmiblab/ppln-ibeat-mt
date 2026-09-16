import logging
import os

import numpy as np

from miblab import pipe
import dbdicom as db
import vreg

from utils import data, dicom

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline


def mtr(array):
  
  # Calculate
  # array[...,0], array[...,1] = MT_OFF & MT_ON
  # MTR = 100*(MToff - MTon)/MToff
  array_mtr = 100*(array[...,0] - array[...,1]) / array[...,0]
  array_mtr[array[...,0] == 0] = 0
  array_mtr[array_mtr > 100] = 100
  #array_mtr[array_mtr < -100] = -100
  array_mtr[array_mtr < 0] = 0
  array_avr = np.mean(array, axis=-1)

  return array_mtr, array_avr


def mtr_map(series, dir_output):

    vol, array = dicom.get_vol_arrays(series, 'MagnetizationTransfer')

    array_mtr, array_avr = mtr(array)

    mtr_vol = vreg.volume(array_mtr, vol.affine)
    avr_vol = vreg.volume(array_avr, vol.affine)

    dicom.save(dir_output, series, 'MTR_map', mtr_vol, None)
    dicom.save(dir_output, series, 'AVR_map', avr_vol, None)


def map_all(dir_input, dir_output):

    print('Loading moco mdr series')
    # Load moco mdr DICOM series
    mt_series = db.series(dir_input, contains = 'moco')

    for series in mt_series:

        print(f"Running on series: {series}")

        # Extract participant ID and study & series descriptions
        participant, study, descr = dicom.get_attributes(series)
        
        # Skip if map already exists for this dataset
        if data.skip_existing(dir_output, participant, study) == True:
            logging.info(f"Series {participant} already exists --- skipping")
            continue

        # Skip if mdr missing for this dataset
        if data.skip_missing(dir_input, participant, study) == True:
            logging.info(f"Series {participant} missing --- skipping")
            continue

        mtr_map(series, dir_output) 


def run(build, logfile):

    logging.info("Stage 1 --- Calculating MTR maps ---")

    for site in ['Leeds', 'Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:

        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='04_mdr')
        patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)
        
        print(f'Mapping {site} patients')
        map_all(patients_input, patients_output)
      
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='04_mdr')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')

    print(f'Mapping controls')
    map_all(controls_input, controls_output)


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage map
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
