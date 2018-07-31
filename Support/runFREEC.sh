#auto freec
BAMdir='/mnt/storage/emedlab/new_MIT_ernest/bam/high_quality_bams/'
IFS=', ' read -r -a SAMPLES <<< `find ${BAMdir}*bam -printf "%f "`
FREEC='/home/matt/scripts/FREEC-11.0/src/freec'
threads=20                                        # Max processes to run. NB. This won't influence threads spawned by child processes.

mkdir -p configs

echo 'Generating config files from base template'
for SAMPLE in ${SAMPLES[@]}; do
	IFS='.' read -r -a SAMPLE <<< ${SAMPLE}
	(cat template.conf ; echo 'mateFile='${BAMdir}${SAMPLE}'.bam') > ./configs/${SAMPLE}.conf
done

pid=()                                            # For holding process IDs
echo 'Running Control-FREEC'
for SAMPLE in ${SAMPLES[@]}; do                # For each of our desired processes
        while [ ${#pid[@]} -ge ${threads} ]; do         # When at max processes, wait until some finish
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
		${FREEC} -conf ./configs/${SAMPLE}.conf
        pid+=($!)                                       # Collect process ID
done

wait
echo 'Done!'