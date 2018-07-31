#!/usr/bin/env python3

# Config for Concordance
import os
import sys
import pandas as pd

accepted_types = ['CNVNATOR','FREEC']

def helpInfo():
    print('=Configure Concordance Outputs for SV-Pop Check=')
    print('  Run as: ConfigConverter.py </path/to/file> <file_type>')

if len(sys.argv) == 1:
    helpInfo()
    sys.exit()
elif len(sys.argv) >= 3:
    input_file = sys.argv[1] #blah.cnvs
    output_file = input_file.split('.')[0] #blah
    input_type = sys.argv[2]
else:
    helpInfo()
    print('Error: Too few arguments provided')

# Check if file exists
if not os.path.isfile(input_file):
    print("Error: Provided file '{0}' does not exist.".format(input_file))
    sys.exit()

# Check if input_type makes sense
if input_type.upper() not in accepted_types:
    print("Error: Provided input type '{0}' does not exist.".format(input_type))
    print("Accepted file types are: {0}".format(accepted_types))
    sys.exit()

# CNVNator input
if input_type.upper() == 'CNVNATOR':
    dat = pd.read_table(input_file)

    # CNVtype \t coordinates \t CNV_site \t normalized_RD \t e-val1 \t e-val2 \t e-val3 \t e-val4 \t q0
    type_dict = {'deletion':'DEL', 'duplication':'DUP'}

    # Clean up concordance dataset, identify variant lengths
    chromosomes, starts, ends = [], [], []
    for index, row in dat.iterrows():
        chrom, start, end = re.findall(r"[\w']+", row['coordinates'])
        chromosomes.append(chrom)
        starts.append(start)
        ends.append(end)
    dat['Chromosome'] = chromosomes
    dat['Start'] = starts
    dat['End'] = ends
    dat['Length'] = abs(dat['End'] - dat['Start'])
    dat['Type'] = [type_dict[x] for x in dat['CNV_type']]
    dat['Source'] = 'CNVNator'

    dat[['Chromosome','Start','End','Length','Type','Source']].to_csv(output_file+'.csv',index=False)

# Control-FREEC input
elif input_type.upper() == 'FREEC':
    dat = pd.read_table(input_file, header=None)

    #Unnamed: Chromosome \t Start \t End \t Count \t Type
    type_dict = {'loss':'DEL', 'gain':'DUP'}

    dat.columns = ['Chromosome', 'Start', 'End', 'CopyNumber', 'Type0']
    dat['Length'] = abs(dat['End'] - dat['Start'])
    dat['Type'] = [type_dict[x] for x in dat['Type0']]
    dat['Source'] = 'FREEC'

    dat[['Chromosome','Start','End','Length','Type','Source']].to_csv(output_file+'.csv',index=False)

# Output as:
## Chromosome,Start,End,Type
