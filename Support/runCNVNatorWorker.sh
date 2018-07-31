# Core CNVNator Pipeline: Worker Process

CNVNATOR='/usr/local/bin/cnvnator'
CHRS='Pf3D7_01_v3 Pf3D7_02_v3 Pf3D7_03_v3 Pf3D7_04_v3 Pf3D7_05_v3 Pf3D7_06_v3 Pf3D7_07_v3 Pf3D7_08_v3 Pf3D7_09_v3 Pf3D7_10_v3 Pf3D7_11_v3 Pf3D7_12_v3 Pf3D7_13_v3 Pf3D7_14_v3'
BAMDIR='/mnt/storage/emedlab/new_MIT_ernest/bam/high_quality_bams/'
BIN_SIZE=300
OUTDIR='./RefDir/' # Reference fastas (split by chr) should live here.
#REGIONSTOEXCLUDE.bed
IFS=', ' read -r -a CHRSARRAY <<< ${CHRS}

# Installation
# https://github.com/indraniel/cnvnator-packager

# Receive passed sample
SAMPLE=$1

# Filter regions from bam
#bedtools intersect -abam ${BAMDIR}${SAMPLE}.bam -b ${REGIONSTOEXCLUDE} -v > ${SAMPLE}_filtered.bam

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
