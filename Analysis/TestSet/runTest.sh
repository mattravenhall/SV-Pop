#!/bin/bash

model='DEL'
annot='./annotation.txt'
inFile='./input.txt'
gapsFile='./excluded.csv'
popsFile='./pheno.txt'

# Perform Test Run
../SVPop --inFile=${inFile} --model=${model} --refFile=${annot} \
	--filterGaps=True --gapsFile=${gapsFile} --subPops=${popsFile} \
	--outFile='./TestRun' --suppressWarnings=False #--multithread=False
# &> ${model}_TestRun.log &
