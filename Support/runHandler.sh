# Get sample IDs
IFS=', ' read -r -a SAMPLES <<< `find /path/to/files/*bam -printf "%f "`

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
	bash runCNVNator.sh ${SAMPLE} &
	pid+=($!)                                       # Collect process ID
done
