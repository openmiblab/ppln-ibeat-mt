import json
import platform

import os
from pathlib import Path
import re

from miblab import pipe


# HELPER FUNCTION(S)
def get_previous(file):

    current_stage = Path(file)

    # Extract number using regex (handles "02", "2", etc.)
    match = re.search(r'(\d+)', current_stage.name)
    if match:
        current_num_str = match.group(1)
        # Calculate previous number and format with leading zeros if necessary
        prev_num = int(current_num_str) - 1
        prev_num_str = str(prev_num).zfill(len(current_num_str))
        
        # Look for file in same directory starting with previous number
        target_pattern = f"stage_{prev_num_str}_*"
        
        try:
            # Get first file that matches pattern
            prev_script = next(current_stage.parent.glob(target_pattern))
            print(f"Found: {prev_script.stem}")
        except StopIteration:
            print(f"No file found matching pattern: {target_pattern}")
        
        return prev_script.stem


def get_pipeline(file, full_path=False):

    full_pipeline = os.path.abspath(file).split(os.sep)[-2]

    if full_path == False:
        return full_pipeline.split('_')[-1]

    else:
        return full_pipeline


def get_ppln_buildpath(file):
    """
    Constructs the absolute path to the local project build folder.
    """
    script_path = Path(file).absolute()
    
    # Go up 4 levels to escape code/ structure and reach overall iBEAt project root
    # e.g.,  ibeat_totspineseg/stage_01_auto_segment.py -> src -> ppln-ibeat-totspineseg -> code -> iBEAt
    project_root = script_path.parents[4]
    
    # Create output build dir
    output_dir = project_root / "build"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def get_external_buildpath(file, pipeline, stage):
    """Reads other pipelines' finished data from the shared build archive.
    Falls back to the local build directory if config.json does not exist.
    """

    script_path = Path(file).absolute()
    
    # Go up 2 levels to reach pipeline root
    # e.g., ibeat_totspineseg/stage_01_auto_segment.py -> src -> ppln-ibeat-totspineseg
    pipeline_root = script_path.parents[2]
    
    config_file = pipeline_root / "config.json"

    # Try reading from shared xdrive
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)
            
        if platform.system() == "Windows":
            external_buildpath = Path(config["WINDOWS_EXTERNAL_BUILD_DIR"]) / pipeline / stage
        else:
            external_buildpath = Path(config["HPC_EXTERNAL_BUILD_DIR"]) / pipeline / stage
    
    else:
        # Fallback to local external build folder if config doesn't exist
        project_root = script_path.parents[4]
        external_buildpath =  project_root / "build" / pipeline / stage

    return external_buildpath


def input_ibeat_dir(build, pipeline, file, group, site=None, specific=False):
    
    if specific == False:
        stage = get_previous(file)
    else:
        stage = f'stage_{specific}'

    if site == None:
        input_dir = os.path.join(build, pipeline, stage, group)
    else:
        input_dir = os.path.join(build, pipeline, stage, group, site)

    os.makedirs(input_dir, exist_ok=True)

    return input_dir


def output_ibeat_dir(build, pipeline, file, group, site=None):

    #dir_base = pipe.stage_output_dir(build, pipeline, file) # doesn't work same on hpc
    # Get filename without extension
    stage = Path(file).stem  # e.g., returns exactly 'stage_01_auto_segment'

    if site == None:
        subdir = os.path.join(build, pipeline, stage, group)
    else:
        subdir = os.path.join(build, pipeline, stage, group, site)
    
    os.makedirs(subdir, exist_ok=True)

    return subdir


def get_related_study(dir_base, series_related):

    related_study = [dir_base, series_related[1], series_related[2]]

    return related_study


def list_participants(path):
  
    participants = [d for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))]

    return participants


def list_studies(path, participant):

    full_path = os.path.join(path, f"Patient__{participant}")
    
    studies = [d for d in os.listdir(full_path)
      if os.path.isdir(os.path.join(full_path, d))] if os.path.exists(full_path) else []
      
    return studies


def skip_existing(path, participant, study):

    participants = list_participants(path)
    if participants == []:
        return False

    studies = list_studies(path, participant)
    if studies == []:
        return False
    else:
        # If dataset already exists, continue to next
        if f'Patient__{participant}' in participants:
            is_present = any(study in item for item in studies)
            if is_present == True:
                print(f'skipping {participant} {study}: already exists')
                return True


def skip_missing(path, participant, study):
  
    participants = list_participants(path)
    if participants == []:
        return True

    studies = list_studies(path, participant)
    if studies == []:
        return True

    # If dataset missing, continue to next
    if f'Patient__{participant}' not in participants:
        is_present = any(study not in item for item in studies)
        if is_present == True:
            print(f'skipping {participant} {study}: missing')
            return True


def list_zip_files(root_folder):
    return [str(p) for p in Path(root_folder).rglob("*.zip")]
