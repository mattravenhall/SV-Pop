# CNVNator Pipeline
CNVNATOR='/usr/local/bin/cnvnator'
CHRS='chr1 chr2 ... chrN'
BAMDIR='/path/to/bams/'
BIN_SIZE=100
IFS=', ' read -r -a CHRSARRAY <<< ${CHRS}

# Installation
# https://github.com/indraniel/cnvnator-packager

# Receive passed sample
SAMPLE=$1

# Extract Reads
${CNVNATOR} -root ${SAMPLE}.root -chrom ${CHRS} -unique -tree ${BAMDIR}${SAMPLE}.bam

echo -e 'CNV_type\tcoordinates\tCNV_site\tnormalized_RD\te-val1\te-val2\te-val3\te-val4\tq0' > ${SAMPLE}.cnvs
for CHR in ${CHRSARRAY[@]}; do
	# Generate histogram
	${CNVNATOR} -root ${SAMPLE}.root -chrom ${CHR} -his ${BIN_SIZE}

	# Calculate statistics
	${CNVNATOR} -root ${SAMPLE}.root -chrom ${CHR} -stat ${BIN_SIZE} > ${SAMPLE}_${CHR}.stats

	# Signal Partioniing
	${CNVNATOR} -root ${SAMPLE}.root -chrom ${CHR} -partition ${BIN_SIZE} >> ${SAMPLE}_${CHR}.stats

	# CNV Calling:
	${CNVNATOR} -root ${SAMPLE}.root -chrom ${CHR} -call ${BIN_SIZE} >> ${SAMPLE}.cnvs

	# Outputs as: <CNV_type coordinates CNV_size normalized_RD e-val1 e-val2 e-val3 e-val4 q0>
	# normalized_RD -- normalized to 1.
	# e-val1        -- is calculated using t-test statistics.
	# e-val2        -- is from the probability of RD values within the region to be in
	# the tails of a gaussian distribution describing frequencies of RD values in bins.
	# e-val3        -- same as e-val1 but for the middle of CNV
	# e-val4        -- same as e-val2 but for the middle of CNV
	# q0            -- fraction of reads mapped with q0 quality
done

# Delete root file to preserve space
rm ./${SAMPLE}.root
