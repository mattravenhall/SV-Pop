#!/bin/bash

# Multi-CNVNator: Run CNVNator for a bunch of .bam files

# Get sample IDs
IFS=', ' read -r -a SAMPLES <<< `find /mnt/storage/emedlab/new_MIT_ernest/bam/high_quality_bams/*bam -printf "%f "`

pid=()                                            # For holding process IDs
threads=20                                        # Max processes to run. NB. This won't influence threads spawned by child processes.

for SAMPLE in ${SAMPLES[@]}; do                # For each of our desired processes
	while [ ${#pid[@]} -ge ${threads} ]; do	        # When at max processes, wait until some finish
		for id in ${pid[@]}; do
			if [ ! -d /proc/${id} ]; then               # If process doesn't exist...
				for i in "${!pid[@]}"; do
					if [[ ${pid[i]} = "${id}" ]]; then
						unset 'pid[i]'                        # Remove finished process IDs from holder
					fi
				done
			fi
		done
		sleep 5
	done
	IFS='.' read -r -a SAMPLE <<< ${SAMPLE}
	bash runCNVNatorWorker.sh ${SAMPLE} &
	pid+=($!)                                       # Collect process ID
done

wait
mv *.stats bin300/
mv *.cnvs bin300/
