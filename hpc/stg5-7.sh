#!/bin/bash   
#SBATCH --mem=128G         
#SBATCH --cpus-per-task=12
#SBATCH --time=95:00:00
#SBATCH --mail-user=ergunwhy1@sheffield.ac.uk
#SBATCH --mail-type=FAIL,END
#SBATCH --job-name=ppln
#SBATCH --output=logs/stg5-7.out
#SBATCH --error=logs/stg5-7.err

# Unsets the CPU binding policy.
# Some clusters automatically bind threads to cores; unsetting it can 
# prevent performance issues if code manages threading itself 
# (e.g. OpenMP, NumPy, or PyTorch).
unset SLURM_CPU_BIND

# Ensures all environment variables from the submission 
# environment are passed into the job’s environment
export SLURM_EXPORT_ENV=ALL

# Loads the Anaconda module provided by the cluster.
# (On HPC systems, software is usually installed as “modules” to avoid version conflicts.)
module load Anaconda3/2024.02-1
module load Python/3.10.8-GCCcore-12.2.0 # essential to load latest GCC

# Initialise Conda for this non-interactive shell
eval "$(conda shell.bash hook)"

# Activates Conda environment named ibeat-mt.
# (Older clusters use source activate; newer Conda versions use conda activate venv.)
# Assumes conda environment 'ibeat-mt' has already been created
conda activate ibeat-mt

# Get current username
USERNAME=$(whoami)

# Define path variables
ENV="/mnt/parscratch/users/$USERNAME/.conda/.envs/ibeat-mt"
CODE="/mnt/parscratch/users/$USERNAME/iBEAt/code/ppln-ibeat-mt/src/ibeat_mt"
BUILD="/mnt/parscratch/users/$USERNAME/iBEAt/build/mt"

# Run python scripts for all stages 5-7 on the allocated compute resources managed by Slurm
srun "$ENV/bin/python" "$CODE/stage_05_map.py" --build="$BUILD"
srun "$ENV/bin/python" "$CODE/stage_06_align.py" --build="$BUILD"
srun "$ENV/bin/python" "$CODE/stage_07_postcheck.py" --build="$BUILD"