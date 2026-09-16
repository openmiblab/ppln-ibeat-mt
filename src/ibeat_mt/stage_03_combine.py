import logging
import os

from miblab import pipe
import dbdicom as db

from utils import data

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline


def get_mag_only(all_series):
  
    if all_series == []:
        logging.error(f"Empty series")
        mag_only = []
        return
    else:
        for series in all_series:
            if 'phase' not in series[-1][0]:
                mag_only = series

    return mag_only


def get_series(study):

    mt_on_all = db.series(study, contains='MT_ON')
    mt_off_all = db.series(study, contains='MT_OFF')

    mt_on, mt_off = get_mag_only(mt_on_all), get_mag_only(mt_off_all)

    return [mt_on], [mt_off]


def check_matching(mt_on, mt_off, dir_output, study):

    # If one is missing, or there are multiple, do not proceed
    if len(mt_on)!=1 or len(mt_off)!=1:
        logging.error(f"Patient {study[1]} - Error: number of MT_ON does not match MT_OFF")
        return
    else:
        mt = [dir_output, study[1], study[2], 'MT']
        return mt


def merge(mt_on, mt, mt_off):
  
    # Merge the two sequences into one
    try:
        db.copy(mt_on[0], mt)
        db.copy(mt_off[0], mt)
    except:
        logging.error(f"Patient {mt} - Error merging")
        return


def combine_all(dir_input, dir_output):

    print('Loading cleaned studies')
    # Load cleaned DICOM studies
    all_studies = db.studies(dir_input)

    for study in all_studies:

        print(f"Running on study: {study}")
      
        participant = study[1] # extract participant ID
        study_name = study[-1][0] # extract study description

        # Skip if combine already exists for this dataset
        if data.skip_existing(dir_output, participant, study_name) == True:
            logging.info(f"Series {participant} already exists --- skipping")
            continue

        # Skip if cleaned database missing for this dataset
        if data.skip_missing(dir_input, participant, study_name) == True:
            logging.info(f"Series {participant} missing --- skipping")
            continue

        mt_on, mt_off = get_series(study)

        if (mt_on == [None]) or (mt_off == [None]):
            print('empty mt_on or mt_off')
            continue

        if check_matching(mt_on, mt_off, dir_output, study) == False:
            continue
        else:
            mt = check_matching(mt_on, mt_off, dir_output, study)
            merge(mt_on, mt, mt_off)


def run(build, logfile):

    logging.info("Stage 1 --- Harmonising data ---")
    
    for site in ['Leeds', 'Bari', 'Bordeaux', 'Exeter', 'Turku', 'Sheffield']:
        patients_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Patients', site, specific='02_clean_database')
        patients_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Patients', site)

        combine_all(patients_input, patients_output)
      
    controls_input = data.input_ibeat_dir(build, PIPELINE, __file__, 'Controls', specific='02_clean_database')
    controls_output = data.output_ibeat_dir(build, PIPELINE, __file__, 'Controls')
    combine_all(controls_input, controls_output)


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage combine
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
