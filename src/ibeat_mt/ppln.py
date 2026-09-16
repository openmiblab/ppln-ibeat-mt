import ibeat_mt as ppln
from miblab import pipe

from utils import data

PIPELINE = data.get_pipeline(__file__)

def run(build, logfile):
    
    ppln.stage_01_download.run(build, logfile)
    ppln.stage_02_clean_database.run(build, logfile)
    ppln.stage_03_combine.run(build, logfile)
    ppln.stage_04_mdr.run(build, logfile)
    ppln.stage_05_map.run(build, logfile)
    ppln.stage_06_align.run(build, logfile)
    ppln.stage_07_display.run(build, logfile)
    ppln.stage_08_measure.run(build, logfile)


if __name__=='__main__':

    BUILD = data.get_output_buildpath(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=str, default=BUILD, help="Build folder")
    args = parser.parse_args()
    
    pipe.run_ppln(run, args.build, PIPELINE)
