#!/bin/bash
#SBATCH --job-name=blast_job
#SBATCH --output blastp_%j.log
#SBATCH -A bsd
#SBATCH -N 1
#SBATCH --ntasks=8
#SBATCH -p burst
#SBATCH --cpus-per-task=4
#SBATCH --mem=4gb
#SBATCH -t 4:00:00
#SBATCH --array=1-100

date;hostname;pwd

 
export INPUT_DIR="input"
export OUTPUT_DIR="output"
export LOG_DIR="logs"
mkdir -p ${OUTPUT_DIR} ${LOG_DIR}
 
RUN_ID=$(( $SLURM_ARRAY_TASK_ID + 1 ))
 
QUERY_FILE=$( ls ${INPUT_DIR} | sed -n ${RUN_ID}p )
QUERY_NAME="${QUERY_FILE%.*}"
 
QUERY="${INPUT_DIR}/${QUERY_FILE}"
OUTPUT="${OUTPUT_DIR}/${QUERY_NAME}.out"
 
echo -e "Command:\nblastp –query ${QUERY} –db /lustre/or-hydra/cades-bsd/4pz/paperblastdb/uniq.faa  –out ${OUTPUT} –evalue 1e-10 –outfmt 6 –num_threads 8"
 
blastp -query ${QUERY} -db /lustre/or-hydra/cades-bsd/4pz/paperblastdb/uniq.faa -out ${OUTPUT} -evalue 1e-5 -outfmt 6 -num_threads 8
 
date
