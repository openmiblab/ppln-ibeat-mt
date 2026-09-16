"""
Automatic download of MT data from XNAT.
"""
import os
import logging

from miblab import pipe
from miblab_data.xnat import download_series

from utils import data, ibeat

# CONSTANTS
PIPELINE = data.get_pipeline(__file__) # get current pipeline


def run(build, logfile):

    logging.info("Stage 1 --- Downloading data ---")
 
    n_max=2
    #n_max=None

    dir_output = pipe.stage_output_dir(build, PIPELINE, __file__)
    cred = os.path.join(os.getcwd(), 'user_XNAT.txt')

    for group, props in ibeat.DOWNLOAD.items():
        try:
            download_series(
                xnat_url="https://qib.shef.ac.uk",
                output_dir=dir_output,
                log=True,
                n_max=n_max,
                cred=cred,
                **props
            )
        except:
            logging.exception(f"Error downloading {group}.")


if __name__ == '__main__':

    # Define root build folder
    BUILD = data.get_ppln_buildpath(__file__)

    # Run mt stage download
    pipe.run_stage(run, BUILD, PIPELINE, __file__)
