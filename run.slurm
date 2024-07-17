#!/bin/bash
#SBATCH --output=_output/%x.%j.out
#SBATCH --nodes=1                                          # node count
#SBATCH --ntasks=1                                          # total number of tasks across all nodes
#SBATCH --cpus-per-task=64                                  # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem-per-cpu=7G                                   # memory per cpu-core (4G is default)
#SBATCH --time=01:00:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-type=fail         # send email if job fails
# #SBATCH -p [h11n1]

module purge
module load anaconda3/2024.2
conda activate cutqc
module load gurobi/10.0.1
export PYTHONPATH=/usr/licensed/gurobi/10.0.1/linux64/lib/python3.8_utf32

perf stat -e fp_arith_inst_retired.256b_packed_single python example.py --circuit_size={circuit_size} --max_subcircuit_width={max_subcircuit_width} --circuit_type={circuit_type}
