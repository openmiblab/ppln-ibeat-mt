import logging
import os

import numpy as np
import pandas as pd

from miblab import pipe
import dbdicom as db
import vreg
import mdreg

from utils import data, dicom, qc

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline


def _mdr(series, array, path, dir_transforms, fit_image, force_2d):

    patient, study, descr = dicom.get_attributes(series)
    site = series[0].split(os.sep)[-1]
    group = series[0].split(os.sep)[-2]

    patient_folder = os.path.join(dir_transforms, patient)
    os.makedirs(patient_folder, exist_ok=True)
    
    filename = f"{patient}_{study}_{descr}"

    fit_coreg = {
            'package': 'ants',
            'type_of_transform': 'SyNOnly',
            'name': filename,
            'path': os.path.join(dir_transforms, patient),
            'outprefix': f"{os.path.join(patient_folder, filename)}_",
            'return_inverse': True
            }

    coreg, fit, transfo, pars = mdreg.fit(array,
                fit_image = fit_image,
                fit_coreg = fit_coreg,
                #maxit = 5,
                maxit = 1,
                force_2d = force_2d,
                verbose = 2,
            )
    
    return fit, coreg, transfo, pars


def mdr_series(series, dir_output, dir_transforms, dir_qc, ier_list, ice_list):

    participant, study, descr = dicom.get_attributes(series)

    vol, array = dicom.get_vol_arrays(series, 'MagnetizationTransfer')

    fit, coreg, transfo, pars = _mdr(series, array, dir_output, dir_transforms,
                                    fit_image=None, force_2d=False)

    fi, mi, ci = qc.convert_to_ants(array, fit, coreg)
    qc.plot_alignment(fi, mi, ci, series, dir_qc)
    ier_row = qc.calculate_ier(fi, transfo, participant)
    ier_list.append(ier_row)

    ice_fieldpath_MTon = qc.calculate_ice('ON', series, dir_output, dir_transforms, transfo, fi, mi)
    ice_fieldpath_MToff = qc.calculate_ice('OFF', series, dir_output, dir_transforms, transfo, fi, mi)

    ice_average_on = qc.plot_ice(series, dir_qc, 'ON', ice_fieldpath_MTon)
    ice_average_off = qc.plot_ice(series, dir_qc, 'OFF', ice_fieldpath_MToff)
    ice_list.append(ice_average_on)
    ice_list.append(ice_average_off)

    dicom.save(dir_output, series, 'mdr_fit', np.array(fit), vol)
    dicom.save(dir_output, series, 'mdr_moco', coreg, vol)


def mdr_all(dir_input, dir_output, dir_transforms, dir_qc):

    print('Loading combined series')
    # Load combined DICOM series
    mt_series = db.series(dir_input)

    ier_list = []
    ice_list = []

    for series in mt_series:

        print(f"Running on series: {series}")

        # Extract participant ID and study & series descriptions
        participant, study, descr = dicom.get_attributes(series)

        # Skip if mdr already exists for this dataset     
        if data.skip_existing(dir_output, participant, study) == True:
            logging.info(f"Series {participant} already exists --- skipping")
            continue

        # Skip if combined mt missing for this dataset
        if data.skip_missing(dir_input, participant, study) == True:
            logging.info(f"Series {participant} missing --- skipping")
            continue

        mdr_series(series, dir_output, dir_transforms, dir_qc, ier_list, ice_list)
    
    metrics_folder = os.path.join(dir_qc, 'metrics')
    os.makedirs(metrics_folder, exist_ok=True)

    ier_df = pd.DataFrame(ier_list)
    ier_df.to_csv(os.path.join(metrics_folder, 'iers.csv'), index=False)

    ice_df = pd.DataFrame(ice_list)
    ice_df.to_csv(os.path.join(metrics_folder, 'ices.csv'), index=False)


def run(build, logfile):

    logging.info("Stage 1 --- Registering images ---")

    patients_qc = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', specific = '05b_qc')

    for site in ['Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:

        # create patient directories
        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific = '03_combine')
        patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)

        patients_transforms = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific = '04a_transforms')
        patients_qc = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', specific = '04b_qc')

        # run mdr
        print(f'Registering {site} patients')
        mdr_all(patients_input, patients_output, patients_transforms, patients_qc)

    # create control directories   
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific = '03_combine')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')
        
    controls_transforms = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific = '04a_transforms')
    controls_qc = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific = '04b_qc')

    # run mdr
    print(f'Registering controls')
    mdr_all(controls_input, controls_output, controls_transforms, controls_qc)


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage mdr
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
