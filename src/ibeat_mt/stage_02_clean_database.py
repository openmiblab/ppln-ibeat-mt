"""
Create clean database
"""
import os
from pathlib import Path
import logging
import tempfile
import zipfile

import re

import numpy as np

import dbdicom as db
from miblab import pipe

from utils import data, ibeat

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline

# HELPER FUNCTION(S)
def remove_ot_bari(participant):

    all_zips = data.list_zip_files(participant)
    zips_minus_OT = [s for s in all_zips if 'OT' not in s]

    return zips_minus_OT


def get_zips(participant, site):

    if site == 'Bari':
        zip_files = remove_ot_bari(participant)
    else:
        zip_files = data.list_zip_files(participant)

    return zip_files


def split_phase_series(series):

    series_split = db.split_series(series, 'ImageType')

    for split in series_split:
        if 'PHASE' in split[0][2]:
            phase_series = split[1]
        else:
            mag_series = split[1]
    
    return phase_series, mag_series


def which_mt(series, site):

    if site == 'Leeds':
        series_scan_option = db.unique('ScanOptions', series)
        if 'MT' in series_scan_option[0]:
            # if ScanOptions = ['PFP', 'MT']
            which_mt = 'ON'
        else:
            # if ScanOptions = ['PFP']
            which_mt = 'OFF'
    else:
        if re.search(r'mt.{1,3}on', series[-1][0], re.IGNORECASE):
            which_mt = 'ON'
        elif re.search(r'mt.{1,3}off', series[-1][0], re.IGNORECASE):
            which_mt = 'OFF'

    return which_mt


def update_tag(shape, value, key):
    
    new_tag = np.full(shape, value).reshape(shape)
    new_values = {key: new_tag}

    return new_values


def increment_series(series_descr, series_list):

    # Increment the number as appropriate
    new_series_descr = series_descr
    print(f"new series = {new_series_descr}")
    counter = 2
    while new_series_descr in series_list:
        new_series_descr = series_descr.replace('_1', f'_{counter}')
        counter += 1
    series_list.append(new_series_descr)

    return new_series_descr


def edit_tag(series, new_series_descr, new_values):

    new_series = series[:-1] + [(new_series_descr, 0)]
    
    vol = db.volume(series)
    db.write_volume(vol, new_series, ref=series)

    db.edit(new_series, new_values, dims='SliceLocation')

    return new_series


def update_mt(series, site, series_list):

    shape = (len(db.values(series, 'ImagesInAcquisition')),)
    #MT_tag = db.values(series, (0x0018, 0x9020))

    mt_type = which_mt(series, site)

    if mt_type == 'ON':
        new_values = update_tag(shape, 'YES', 'MagnetizationTransfer')
    if mt_type == 'OFF':      
        new_values = update_tag(shape, 'NO', 'MagnetizationTransfer')

    series_prefix = f'MT_{mt_type}'
    
    series_image_type = db.unique('ImageType', series)

    # e.g., Bari has phase and mag series
    if 'PHASE' in series_image_type[0][2]:
        series_descr = f"{series_prefix}_phase_1"
    else:
        series_descr = f"{series_prefix}_1"
    
    new_series_descr = increment_series(series_descr, series_list)
    new_series = edit_tag(series, new_series_descr, new_values)

    return new_series_descr, new_series


def save_new_series(zip_file, new_series, group, site, new_descr, dir_output, series_exisiting):

    pt_id_clean = ibeat.clean_patient_id(new_series, group, site)
    st_desc_clean = ibeat.clean_study_desc(zip_file, new_series, group, site)
    series_clean = [dir_output, pt_id_clean, (st_desc_clean, 0), (new_descr, 0)]

    if series_clean not in series_exisiting:
        db.copy(new_series, series_clean)
        logging.info(f"Created series {series_clean} --- from file {zip_file}")
    else:
        logging.info(f"Series {series_clean} already exists --- skipping")


def unzip_xnat(participant, dir_output, group, site):

    print('Loading downloaded series')
    # Load downloaded DICOM series    
    series_exisiting = db.series(dir_output)

    zip_files = get_zips(participant, site)

    series_list = []
    
    for zip_file in zip_files:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                series_xnat = db.series(temp_dir)

                for series in series_xnat:

                    print(f"Running on series: {series}")

                    manufacturer = db.unique('Manufacturer', series)[0]

                    if 'philips' in manufacturer.lower(): # Bari, Turku
                        phase_series, mag_series = split_phase_series(series)

                        # save updated phase series
                        phase_descr, phase_new = update_mt(phase_series, site, series_list)
                        save_new_series(zip_file, phase_new, group, site, phase_descr,
                                        dir_output, series_exisiting)

                        # save updated mag series
                        mag_descr, mag_new = update_mt(mag_series, site, series_list)
                        save_new_series(zip_file, mag_new, group, site, mag_descr,
                                        dir_output, series_exisiting)

                    else:
                        new_descr, new_series = update_mt(series, site, series_list)
                        save_new_series(zip_file, new_series, group, site, new_descr,
                                        dir_output, series_exisiting)

        except zipfile.BadZipFile:
                logging.error(f"Invalid zip file: {zip_file}. ")
        except:
                logging.exception(f"Unknown exception while cleaning {zip_file}. ")


def run(build, logfile):

    logging.info("Stage 1 --- Clean and unzip XNAT data ---")
    
    for group, props in ibeat.DOWNLOAD.items():
        site = props['project_id'].split('-')[-1]

        if site == 'Sheffield':
            dir_input = data.input_ibeat_dir(build, PIPELINE, __file__, props['project_id'], specific='01_download')
            dir_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)
        else:
            dir_input = data.input_ibeat_dir(build, PIPELINE, __file__, props['project_id'], props['subject_label'], specific='01_download')

            if 'patient'.lower() in props['subject_label'].lower():
                dir_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)
            else:
                dir_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')

        participants = [f.path for f in os.scandir(dir_input) if f.is_dir()]

        for participant in participants:
            unzip_xnat(participant, dir_output, group, site)


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage clean_database
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
