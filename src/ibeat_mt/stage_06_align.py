import logging
import os
from pathlib import Path

from miblab import pipe
import dbdicom as db
import vreg

import numpy as np

from utils import data, dicom, dixon

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline


def get_binaries(vol, i):

  binary_mask = (vol.values==i).astype(np.float32)
  if np.sum(binary_mask) == 0:
    logging.error(f"Patient {patient} - Error: binary mask is equal to zero")
    return
  else:
    return binary_mask


def get_objects(mask_vol, roi, dixon_vol):
  
  # Binary masks
  binary_mask = get_binaries(mask_vol, roi)

  binary_vol = vreg.volume(binary_mask, mask_vol.affine)

  return binary_vol


def crop_binary(binary_vol, dixon_vol):

  resliced = binary_vol.slice_like(dixon_vol)

  # Use bounding boxes speed up the computation
  cropped = resliced.bounding_box()

  return cropped


def get_spinal_objects(mask_vol, dixon_vol):

    class_map = {
                "background": 0,
                "vertebrae_and_discs": 1, 
                "spinal_cord": 2
            }
            
    vert = get_objects(mask_vol, class_map["vertebrae_and_discs"], dixon_vol)
    sc = get_objects(mask_vol, class_map["spinal_cord"], dixon_vol)
    
    spine = vert.slice_like(dixon_vol).add(sc)

    # Use bounding boxes speed up the computation
    spine = spine.bounding_box()
    vert = vert.bounding_box()
    sc = sc.bounding_box()

    return spine, vert, sc


def get_kidney_objects(mask_vol, dixon_vol):

  class_map = {"kidney_left": 1, "kidney_right": 2}

  rk = get_objects(mask_vol, class_map["kidney_right"], dixon_vol)
  lk = get_objects(mask_vol, class_map["kidney_left"], dixon_vol)
  
  bk = lk.slice_like(dixon_vol).add(rk)

  # Use bounding boxes speed up the computation
  bk = bk.bounding_box()
  lk = lk.bounding_box()
  rk = rk.bounding_box()

  return bk, lk, rk


def _kidneycoreg(atr_vol, bk, lk, rk):

  # Settings
  options = {'coords': 'volume'}
  optimizer = {'method': 'brute'}

  # Translate to both kidneys
  optimizer['grid'] = [[-20, 20, 20], # from -20 to 20 mm in 20 steps in x directions (in-plane)
                       [-20, 20, 20], # from -20 to 20 mm in 20 steps in y directions (in-plane)
                       [-5, 5, 5]] # from -5 to 5 mm in 5 steps in z directions (through-plane)
  print('Coregistering to both kidneys') # ~30-40 mins locally
  tbk = atr_vol.find_translate_to(bk, optimizer=optimizer, **options)
  volume = atr_vol.translate(tbk, **options)

  optimizer['grid'] = 3*[[-2, 2, 10]] # from -2 to 2 mm in 10 steps in all directions
  print('Coregistering to left kidney') # ~15-20 mins locally
  tlk = volume.find_translate_to(lk, optimizer=optimizer, **options)
  print('Coregistering to right kidney') # ~15-20 mins locally
  trk = volume.find_translate_to(rk, optimizer=optimizer, **options)

  # Return affines for each kidney
  return tbk, {
                'LK': volume.translate(tlk, **options).affine,
                'RK': volume.translate(trk, **options).affine,
                }


def align_all(dir_input, dir_output, dir_dixon, dir_kidney):

    print('Loading dixon series')
    # Load dixon DICOM series
    dixon_series = db.series(dir_dixon)

    dixon_csv = os.path.join(os.getcwd(), 'src', 'data', 'dixon_data.csv')
    print('dixon csv path assigned')

    if not os.path.isfile(dixon_csv):
        dixon.download_record()
    # List of selected dixon series
    record = dixon.dixon_record()

    # Loop over the dixon water series
    for series in dixon_series:

        print(f"Running on series: {series}")

        # Skip if series is not a dixon water series
        if 'water' not in series[-1][0]:
            continue

        # Extract participant ID and study & series descriptions
        participant, study, descr = dicom.get_attributes(series)

        print('checking series match')
        participant_errors = ['4128_054', '2128_009', '7128_038', '7128_127']
        if participant in participant_errors:
           continue

        # Skip if align already exists for this dataset
        if data.skip_existing(dir_output, participant, study) == True:
            logging.info(f"Series align {participant} already exists --- skipping")
            continue

        # Skip if map missing for this dataset
        if data.skip_missing(dir_input, participant, study) == True:
            logging.info(f"Series mt {participant} missing --- skipping")
            continue

        # Skip if dixon missing for this dataset
        if data.skip_missing(dir_dixon, participant, study) == True:
            logging.info(f"Series dixon {participant} missing --- skipping")
            continue

        # Skip if kidney masks missing for this dataset
        if data.skip_missing(dir_kidney, participant, study) == True:
            logging.info(f"Series kidney {participant} missing --- skipping")
            continue

        # Skip if it is not the right sequence
        print('checking correct dixon')
        selected_sequence = dixon.dixon_series_desc(record, participant, study)
        if descr[:-6] != selected_sequence:
            continue

        dixon_vol = db.volume(series)
    
        # get other studies
        kidney_study = data.get_related_study(dir_kidney, series)
        mtr_study = data.get_related_study(dir_input, series)

        # get other series
        kidney_series = kidney_study + [('kidney_masks', 0)]
        atr_series = mtr_study + [('AVR_map', 0)]
        mtr_series = mtr_study + [('MTR_map', 0)]

        # get other vols
        print('creating vols')
        kidney_vol = db.volume(kidney_series)
        try:
            atr_vol = db.volume(atr_series)
            mtr_vol = db.volume(mtr_series)
        except Exception as e:
            logging.error(f"Participant {participant} - error reading I-O {study} atr/mtr vol: {e}")
            continue

        # align kidneys
        print('getting kidney objects')
        bk, lk, rk = get_kidney_objects(kidney_vol, dixon_vol)
        print('aligning kidneys')
        tbk, kidney_affine = _kidneycoreg(atr_vol, bk, lk, rk)

        rois = ['LK','RK']

        for region in rois:
            print('setting affines')
            atr_align_vol = atr_vol.set_affine(kidney_affine[region])
            mtr_align_vol = mtr_vol.set_affine(kidney_affine[region])
            print('saving aligned masks')
            dicom.save(dir_output, atr_series, f'atr_{region}_align', atr_align_vol, None)
            dicom.save(dir_output, mtr_series, f'mtr_{region}_align', mtr_align_vol, None)


def run(build, logfile):

    logging.info("Stage 1 --- Aligning (co-reg) masks ---")

    # Import external pipelines
    # dixon data (anatomical ref)
    dixon_ppln = data.get_external_buildpath(__file__, 'dixon', 'stage_5_clean_dixon_data')

    # kidney masks
    kidneyvol_ppln = data.get_external_buildpath(__file__, 'kidneyvol', 'stage_3_edit')

    # data from root folder (same pipeline)
    for site in ['Leeds', 'Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:

        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='05_map')
        patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)

        dir_dixon = os.path.join(dixon_ppln, 'Patients', site)
        dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Patients', site)

        print(f'Aligning {site} patients')
        align_all(patients_input, patients_output, dir_dixon, dir_kidneyvol)
      
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='05_map')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')

    dir_dixon = os.path.join(dixon_ppln, 'Controls')
    dir_kidneyvol = os.path.join(kidneyvol_ppln, 'Controls')

    print(f'Aligning controls')
    align_all(controls_input, controls_output, dir_dixon, dir_kidneyvol)


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage align
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
