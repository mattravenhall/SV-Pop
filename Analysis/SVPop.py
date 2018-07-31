#!/usr/bin/env python3

#####################################################################
# SV-Pop: Population-Based Structural Variant Analysis & Annotation #
#  Matt Ravenhall                                                   #
#                                                                   #
# Requirements:                                                     #
#   -Python 3.4+                                                    #
#   -Pandas 0.18+                                                   #
#   -Numpy 1.10.4+                                                  #
#####################################################################

# NB: Read number pull lines are currently commented, consider including.
# NB: Frequency statistic is calculated as percentage of parsed, not given, samples.
# TODO: Consider a more flexible 'merge variants' function (merges variants with similar positions (ie. start and end within Xbp)).
# TODO: Consider combining the inFile (vcf paths) and pheno file (subPop info), perhaps with a 'PATH' column which 'SAMPLE' is inferred from.

VERSION_NUM =  '1.0' #'1.4.17'
VERSION_NAME = 'Hello World'
VERSION_NOTES = 'First public release.'

import gc
import os
import re
import sys
import datetime
from itertools import compress
from multiprocessing import Pool

# set defaults
reqArgs = ['model','inFile','refFile']
chrSubset = ''
runType = 'STANDARD'

# Stats variables
MODEL = ''
subPops = ''

# File variables
inFile = ''                     # post-delly list of .vcf files
outFile = 'outFile'
gapsFile = ''
variantFile = ''

# Decision booleans
writeVariants = True            # toggle for outputting the per-variant .stats file
writeWindows = True             # toggle for outputting the windows-based stats file
doAnnotation = True             # toggle for annotating file (perhaps link to whether a reference annotation file is provided)
IncludeReads = False
MoreQual = True
PullPhasing = True
suppressWarnings = True
quietConcordance = True
filterGaps = False              # requires accompanying gaps file
windowType = 'popCount'         # 'variantCount' or 'popCount', hidden option. variantCount will break frequencies.
writeSamples = True
mergeChr = True
doFst = True
calcScore = True

# Window variables
windowSize  = 1000
windowStep  = 500
minLength   = 0
maxLength   = 100000            # max length of variants (ie. wipe out the weird whole chromosome stuff does)

# Annotation variables
RefFile     = ''                # reference, cleaned, annotation file
refFormat   = 'tsv'
refType     = 'gene'            # type of information to annotate with, e.g. feature_type
refTypeID   = 'gene_name'
refCol      = 'Feature'

# Filtering variables
doFiltering = True
minimumQuality  = 0.9
minimumPrecision = None
maximumPercRef = 0.1
maximumPercHet = 0.3
excludeDupPercHet = False
minimumPercAlt = None
maximumPercMissing = 0.1
removeIntergenic = False
minimumPE = 0
minimumSR = 0
minimumMAPQ = 0
filterScore = False

# Subset variables
region = None
feature = None

# Verification by concordance
filterConcordance = False   # whether to perform check
dirConcordance = './'       # path with secondary discovery files (per-sample)
overlapConcordance = 0.8    # percentage overlap of variants for confirmation
percConcordance = 0         # percentage per-variant for filtering

# Multi-processing
global multithread
multithread = True
threads = os.cpu_count()
# allow numThreads selection via argument

# Colours
showColours = True if '--noCols' not in sys.argv else False
if showColours:
    colTitle = '\033[92m'
    colHelp  = '\033[93m'
    colInfo  = '\033[94m'
    colTime  = '\033[96m'
    colWarn  = '\033[90m'
    colError = '\033[91m'
    colReset = '\033[0m'
    colDone  = '\033[92m'
else: # Just in case we want to toggle colours later
    colTitle = colHelp = colInfo = colTime = colWarn = colError = colReset = colDone = ''

if __name__ == "__main__":
    print('\n{colTitle}SV-Pop: Population-Based Structural Variation Analysis And Annotation{colReset}'.format(**globals()),flush=True)
    print('{colTitle}  Version {0} - "{1}"{colReset}'.format(VERSION_NUM, VERSION_NAME, **globals()),flush=True)

    if ('-v' in sys.argv) or ('--version' in sys.argv):
        print('{colTitle}  Version Notes: {0}{colReset}\n'.format(VERSION_NOTES, **globals()),flush=True)
        sys.exit()
    print()
    if len(sys.argv) <= 1: # ie. if no arguments were passed
        print("{colError} Error: No arguments supplied. Request help with '-h' or '--help'.{colReset}\n".format(**globals()),flush=True)
        sys.exit()
    if ('-h' in sys.argv) or ('--help' in sys.argv): # ie. if no arguments were passed
        print(('{colHelp} Default Help Page.\n\n'+
        '{colInfo} Usage: SVPop.py --command=argument\n'+
        '\n Required Arguments\n'+
        '  --inFile, -F\t\tFile containing a list of vcf files from DELLY.\n'+
        '  --model, -M\t\tDELLY model. (DUP,DEL,INS,INV)\n'+
        '  --refFile, -R\t\tAnnotation reference file. (gtf,gff,csv,tsv)\t\t(if doAnnotation is True)\n'+ # Must be formatted with four columns (Chromosome, Start, End, Gene)
        '\n Additional Arguments\n'+
        "  --subPops, -P\t\tTab-seperated file with 'Samples' and sub-pop columns.\n"+
        '  --refFormat\t\tBypass reference format detection. (gtf,gff,csv,tsv)\t(default:{refFormat})\n'+
        '  --refType\t\tSpecify a feature type to annotate with. (gtf/gff only)\t(default:{refType})\n'+
        '  --refTypeID\t\tSpecify a feature ID to annotate with. (gtf/gff only)\t(default:{refType})\n'+
        '  --chr\t\t\tSpecify a subset of chromosomes, separated by commas.\t(default:All)\n'+
        '\n Output Formatting\n'+
        "  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:{outFile})\n"+
        '  --writeVariants\tWhether to write out pre-windows variants file.\t\t(default:{writeVariants})\n'+
        '  --writeWindows\tWhether to write out windows stats file.\t\t(default:{writeWindows})\n'+
        '  --doAnnotation\tWhether to annotate the final output.\t\t\t(default:{doAnnotation})\n'+
        '  --includeReads\tWhether to include median read counts.\t\t\t(default:{IncludeReads})\n'+
        '  --moreQuality\t\tWhether to include PE count, SR count and median MAPQ.\t(default:{MoreQual})\n'+
        '  --suppressWarnings\tWhether to silence warning messages (not errors).\t(default:{suppressWarnings})\n'+
        '  --filterGaps\t\tWhether to remove variants overlapping known gaps.\t(default:{filterGaps})\n'+
        '  --gapsFile\t\tReference csv with gap chromosome, start and ends.\n'+
        '  --writeSamples\tWhether to write out sample IDs with each variant.\t(default:{writeSamples})\n'+
        '  --mergeChr\t\tMerge per-chromosome files into one file.\t\t(default:{mergeChr})\n'+
        '  --doFst\t\tWhether to calculate Fst values for sub-populations.\t(default:{doFst})\n'+
        '  --calcScore\t\tWhether to include SVPop per-variant scoring.\t\t(default:{calcScore})\n'+
        '\n Numerical Variables\n'+
        '  --windowSize\t\tWindow size.\t\t\t\t\t\t(default:{windowSize})\n'+
        '  --windowStep\t\tWindow step.\t\t\t\t\t\t(default:{windowStep})\n'+
        '\n Filtering Options\n'+
        '  --doFiltering\t\tApply filtering step prior to output.\t\t\t(default:{doFiltering})\n'+
        '  --minLength\t\tMinimum length of structural variants.\t\t\t(default:{minLength})\n'+
        '  --maxLength\t\tMaximum length of structural variants.\t\t\t(default:{maxLength})\n'+
        '  --minimumQuality\tMinimum threshold for Quality column.\t\t\t(default:{minimumQuality})\n'+
        '  --minimumPrecision\tMinimum threshold for Precision column.\t\t\t(default:{minimumPrecision})\n'+
        '  --maximumPercRef\tMaximum threshold for perc homozygous reference.\t(default:{maximumPercRef})\n'+
        '  --maximumPercHet\tMaximum threshold for perc heterozygous.\t\t(default:{maximumPercHet})\n'+
        '  --minimumPercAlt\tMinimum threshold for perc homozygous alternative.\t(default:{minimumPercAlt})\n'+
        '  --maximumPercMissing\tMaximum threshold for perc homozygous missing.\t\t(default:{maximumPercMissing})\n'+
        '  --removeIntergenic\tWhether to remove purely intergenic variants.\t\t(default:{removeIntergenic})\n'+
        '  --excludeDupPercHet\tWhether to exclude dups from PercHet filter.\t\t(default:{excludeDupPercHet})\n'+
        '  --minimumPE\t\tMinimum supporting paired reads per-sample per-variant.\t(default:{minimumPE})\n'+
        '  --minimumSR\t\tMinimum supporting split reads per-sample per-variant.\t(default:{minimumSR})\n'+
        '  --minimumMAPQ\t\tMinimum median mapping quality per-sample per-variant.\t(default:{minimumMAPQ})\n'+
        '  --filterScore\t\tMinimum required score, under which to filter variants.\t(default:{filterScore})\n'+
        '\n Verification by Concordance\n'+
        '  --filterConcordance\tWhether to filter variants by concordance.\t\t(default:{filterConcordance})\n'+
        '  --dirConcordance\tPath to directory containing secondary variant files.\t(default:{dirConcordance})\n'+
        '  --overlapConcordance\tProportion of overlap required for verification.\t(default:{overlapConcordance})\n'+
        '  --percConcordance\tPercentage of concordance required per-variants.\t(default:{percConcordance})\n'+
        '\n Multi-Processing\n'+
        '  --multithread\t\tWhether to split analysis over multiple cores.\t\t(default:{multithread})\n'+
        '  --threads\t\tNumber of cores to utilise when multi-processing.\t(default:{threads})\n'+
        '\n Misc. Options\n'+
        '  --help, -h\t\tDisplay this information.\n'+
        '  --version, -v\t\tDisplay full version information.\n'+
        '\n Alternative Pipelines\n'+ # Consider an 'ANNOTATE' function
        '  --CONVERT\t\tConvert a variant output file into a window file.\n'+
        '  --FILTER\t\tFilter a variant output file by a range of factors.\n'+
        '  --MERGE-CHR\t\tMerge per-chromosome variants files into one file.\n'+
        '  --MERGE-MODEL\t\tMerge by-model variants files into one file.\n'+
        '  --SUBSET\t\tCreate a subset of a given variant or window file.\n'+
        '  --STATS\t\tProduce summary statistics for a variant or window files.\n'+
        '  --PREPROCESS\t\tProcess analysis output files for visualisation.{colReset}\n').format(**globals()),flush=True)
        #'  --REGION-SP\t\t[Not Implemented] Convert a variant output file to a Specific-Position encoded sample-oriented file.\n'+
        #'  --REGION-GE\t\t[Not Implemented] Convert a variant output file to a Gene-Encountered encoded sample-oriented file.\n'+
        sys.exit()
    elif len(sys.argv) == 2 and ('--CONVERT' in sys.argv): # CONVERT specific help
        # TODO: Allow CONVERT to handle window file input?
        print(('{colHelp} [--CONVERT] Convert A Variant File Into A Window File\n\n'+
        '{colInfo} Usage: SVPop.py --CONVERT --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPath for variant file being converted.\n'+
        '  --refFile, -R\t\tAnnotation reference file. (gtf,gff,csv,tsv)\t\t(if doAnnotation is True)\n'+ # Must be formatted with four columns (Chromosome, Start, End, Gene)
        '\n Optional Arguments\n'+
        "  --subPops, -P\t\tTab-seperated file with 'Samples' and sub-pop columns.\n"+
        '  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:{outFile})\n'+
        '  --doAnnotation\tWhether to annotate the final output.\t\t\t(default:{doAnnotation})\n'+
        '  --windowSize\t\tWindow size.\t\t\t\t\t\t(default:{windowSize})\n'+
        '  --windowStep\t\tWindow step.\t\t\t\t\t\t(default:{windowStep}){colReset}\n').format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--MERGE-CHR' in sys.argv): # MERGE specific help
        print(('{colHelp} [--MERGE-CHR] Merge Chromosome-Specific Variant or Window Files Together\n\n'+
        '{colInfo} Usage: SVPop.py --MERGE-CHR --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPaths for files to merge (file with path-per-line or comma-separated string).\n'+
        '     Nb. Specifying "<MODEL>v" or "<MODEL>w" will pull all current directory variant or windows files of that model.\n'+
        '  --model, -M\t\tDELLY model. (DUP,DEL,INS,INV). Inferred if missing.\n'+
        '\n Optional Arguments\n'+
        "  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:'Merged'){colReset}\n").format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--MERGE-MODEL' in sys.argv): # MERGE specific help
        print(('{colHelp} [--MERGE-MODEL] Merge Model-Specific Variant or Window Files Together\n\n'+
        '{colInfo} Usage: SVPop.py --MERGE-MODEL --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPaths for files to merge (file with path-per-line or comma-separated string).\n'+
        '     Nb. Specifying "variants" or "windows" will pull all current directory variant or windows files.\n'+
        '  --model, -M\t\tDELLY model. (DUP,DEL,INS,INV). Inferred if missing.\n'+
        '  --chr\t\t\tSpecify chromosome of files, used for output file name.\n'+
        '\n Optional Arguments\n'+
        "  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:'Merged'){colReset}\n").format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--FILTER' in sys.argv): # FILTER specific help
        print(('{colHelp} [--FILTER] Filter Variant Files By Quality, Precision & Inferred Genotype Scores.\n\n'+
        '{colInfo} Usage: SVPop.py --FILTER --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPath for variant file being filtered.\n'+
        '  --model, -M\t\tDELLY model. (DUP,DEL,INS,INV). Inferred if missing.\n'+
        '\n Optional Arguments\n'+
        "  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:'Filtered')\n"+
        '\n Filtering Parameters\n'+
        '  --minimumQuality\tMinimum threshold for Quality column.\t\t\t(default:{minimumQuality})\n'+
        '  --minimumPrecision\tMinimum threshold for Precision column.\t\t\t(default:{minimumPrecision})\n'+
        '  --maximumPercRef\tMaximum threshold for perc homozygous reference.\t(default:{maximumPercRef})\n'+
        '  --maximumPercHet\tMaximum threshold for perc heterozygous.\t\t(default:{maximumPercHet})\n'+
        '  --minimumPercAlt\tMinimum threshold for perc homozygous alternative.\t(default:{minimumPercAlt})\n'+
        '  --maximumPercMissing\tMaximum threshold for perc homozygous missing.\t\t(default:{maximumPercMissing})\n'+
        '  --removeIntergenic\tWhether to remove purely intergenic variants.\t\t(default:{removeIntergenic})\n'+
        '  --percConcordance\tPercentage concordance required per variant.\t\t(default:{percConcordance}){colReset}\n').format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--SUBSET' in sys.argv): # MERGE specific help
        print(('{colHelp} [--SUBSET] Create a subset of a given variant or window file.\n\n'+
        '{colInfo} Usage: SVPop.py --SUBSET --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPath for file to subset from.\n'+
        '  --feature\t\tID or name of gene, ie. a gene. which to subset to.\n'+
        "  --region\t\tRegion to subset to, formatted as 'chromosome:basepairA-basepairB'.\n"+
        '\n Optional Arguments\n'+
        "  --outFile, -O\t\tOutput file name (shared for all outputs).\t\t(default:'Subset'){colReset}\n").format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--PREPROCESS' in sys.argv):
        print(('{colHelp} [--PREPROCESS] Process analysis output files to transition to visualisation.\n\n'+
        '{colInfo} Usage: SVPop.py --PREPROCESS --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPrefix identifying analysis output files for conversion (must be annotated).{colReset}\n').format(**globals()),flush=True)
        sys.exit()
    elif len(sys.argv) == 2 and ('--STATS' in sys.argv):
        print(('{colHelp} [--STATS] Produce summary statistics for variant or window files.\n\n'+
        '{colInfo} Usage: SVPop.py --STATS --parameter=value\n'+
        '\n Required Arguments\n'+
        '  --variantFile\t\tPrefix identifying analysis output files for summary.'+
        '\n Optional Arguments\n'+
        "  --subPops, -P\t\tList of 'Samples' for improving per sample calculation.{colReset}\n").format(**globals()),flush=True)
        sys.exit()
    else:
        import numpy as np
        import pandas as pd
        args = sys.argv[1:]

# Check for duplicate arguments
startArgs = [i.split('=')[0] for i in args]
if len(set(startArgs)) < len(startArgs):
    print('{colError}Error: Duplicate arguments supplied.{colReset}\n'.format(**globals()),flush=True)
    sys.exit()

# # Memory logger
# def memlog(info=''):
#     import time
#     import psutil

#     if not os.path.isfile('usage.log'):
#         with open('usage.log', 'a') as f:
#             f.write('Time,CPU,Memory,Info\n')

#     ctime = time.time()
#     cpu = psutil.Process(os.getpid()).cpu_percent()
#     memory = psutil.Process(os.getpid()).memory_info()[1]/2.**30

#     with open('usage.log', 'a') as f:
#         f.write('{0},{1},{2},{3}\n'.format(ctime,cpu,memory,info))

# Time checker
def printT(message, flush=True, file=sys.stdout):
    print(datetime.datetime.now().strftime('{colTime}[%d-%b-%Y %H:%M:%S]{colReset} '.format(**globals())+message),flush=flush, file=file)

# Write-over time checker, override if multiprocessing.
if not multithread:
    def printR(message, file=sys.stdout):
        sys.stdout.write('\r                                                                                ')
        sys.stdout.write('\r'+datetime.datetime.now().strftime('{colTime}[%d-%b-%Y %H:%M:%S]{colReset} '.format(**globals())+message))
        sys.stdout.flush()
else:
    def printR(message, file=sys.stdout):
        printT(message, file=file)

# set user-indicated variables
def checkArg(valueGiven, givenArg, isBool=False):
    try:
        outValue = valueGiven.split('=')[1]
    except IndexError:
        print('{colError}Error: No argument supplied to {0}.{colReset}\n'.format(givenArg, **globals()),flush=True)
        sys.exit()
    if outValue == '':
        print('{colError}Error: No argument supplied to {0}.{colReset}\n'.format(givenArg, **globals()),flush=True)
        sys.exit()
    if isBool and (outValue.lower() in ['t','true']):
        return(True)
    elif isBool and (outValue.lower() in ['f','false']):
        return(False)
    elif isBool:
        print('{colError}Error: Incorrect argument "{0}" supplied to {1}.{colReset}\n'.format(outValue, givenArg, **globals()),flush=True)
        sys.exit()
    else:
        return(outValue)

for arg in args:
    if arg.startswith('--model') or arg.startswith('-M'):
        MODEL = checkArg(arg,'--model')
        reqArgs.remove('model')
    elif arg.startswith('--subPops') or arg.startswith('-P'):
        subPops = checkArg(arg,'--subPops')
    elif arg.startswith('--inFile') or arg.startswith('-F'):
        inFile = checkArg(arg,'--inFile')
        if len(inFile.split(',')) > 1 or inFile.endswith('.vcf'):
            samples = inFile.split(',')
        else:
            samples = [line.rstrip('\n') for line in open(inFile)]
        reqArgs.remove('inFile')
    elif arg.startswith('--outFile') or arg.startswith('-O'):
        outFile = checkArg(arg,'--outFile')
    elif arg.startswith('--writeVariants'):
        writeVariants = checkArg(arg,'--writeVariants',True)
    elif arg.startswith('--writeWindows'):
        writeWindows = checkArg(arg,'--writeWindows',True)
    elif arg.startswith('--doAnnotation'):
        doAnnotation = checkArg(arg,'--doAnnotation',True)
        if doAnnotation == False and 'refFile' in reqArgs:
            reqArgs.remove('refFile')
    elif arg.startswith('--windowSize'):
        windowSize = int(checkArg(arg,'--windowSize'))
    elif arg.startswith('--windowStep'):
        windowStep = int(checkArg(arg,'--windowStep'))
    elif arg.startswith('--refFile') or arg.startswith('-R'):
        RefFile = checkArg(arg,'--refFile')
        doAnnotation = True # If a refFile is provided, assume annotation is happening
        reqArgs.remove('refFile')
    elif arg.startswith('--refFormat'):
        refFormat = checkArg(arg,'--refFormat')
    elif arg.startswith('--refType'):
        refType = checkArg(arg,'--refType')
    elif arg.startswith('--refTypeID'):
        refTypeID = checkArg(arg,'--refTypeID')
    elif arg.startswith('--chr'):
        chrSubset = checkArg(arg,'--chr').split(',')
    elif arg.startswith('--includeReads'):
        IncludeReads = checkArg(arg,'--includeReads',True)
    elif arg.startswith('--suppressWarnings'):
        suppressWarnings = checkArg(arg,'--suppressWarnings',True)
    elif arg.startswith('--filterGaps'):
        filterGaps = checkArg(arg,'--filterGaps',True)
        if filterGaps:
            reqArgs.append('gapsFile')
    elif arg.startswith('--gapsFile'):
        gapsFile = checkArg(arg,'--gapsFile')
        if filterGaps:
            reqArgs.remove('gapsFile')
        else:
            filterGaps = True
    elif arg.startswith('--writeSamples'):
        writeSamples = checkArg(arg,'--writeSamples',True)
    elif arg.startswith('--windowType'):
        windowType = checkArg(arg,'--windowType')
        if windowType.lower() == 'variantCount':
            print("{colWarn}Warning: 'variantCount' windowType is deprecated and untested.{colReset}".format(**globals()),flush=True)
        if windowType.lower() not in ['popcount','variantcount']:
            print("{colError}Error: Given windowType invalid. Please indicate either 'popcount' or 'variantCount'.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--excludeDupPercHet'):
        excludeDupPercHet = checkArg('--excludeDupPercHet',True)
    elif arg.startswith('--minLength'):
        minLength = int(checkArg(arg,'--minLength'))
    elif arg.startswith('--maxLength'):
        maxLength = int(checkArg(arg,'--maxLength'))
    elif arg.startswith('--minimumQuality'):
        try:
            minimumQuality = float(checkArg(arg,'--minimumQuality'))
        except:
            print("{colError}Error: Given minimumQuality invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--minimumPrecision'):
        try:
            minimumPrecision = float(checkArg(arg,'--minimumPrecision'))
        except:
            print("{colError}Error: Given minimumPrecision invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--maximumPercRef'):
        try:
            maximumPercRef = float(checkArg(arg,'--maximumPercRef'))
        except:
            print("{colError}Error: Given maximumPercRef invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--maximumPercHet'):
        try:
            maximumPercHet = float(checkArg(arg,'--maximumPercHet'))
        except:
            print("{colError}Error: Given maximumPercHet invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--maximumPercMissing'):
        try:
            maximumPercMissing = float(checkArg(arg,'--maximumPercMissing'))
        except:
            print("{colError}Error: Given maximumPercMissing invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--minimumPercAlt'):
        try:
            minimumPercAlt = float(checkArg(arg,'--minimumPercAlt'))
        except:
            print("{colError}Error: Given minimumPercAlt invalid. Value must be numeric.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--removeIntergenic'):
        removeIntergenic = checkArg(arg,'--removeIntergenic')
        if removeIntergenic.upper() == 'TRUE':
            removeIntergenic = True
        elif removeIntergenic.upper() == 'FALSE':
            removeIntergenic = False
        else:
            print("{colError}Error: Provided removeIntergenic invalid. Value must be boolean.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
    elif arg.startswith('--variantFile'):
        variantFile = checkArg(arg,'--variantFile')
    elif arg.startswith('--feature'):
        feature = checkArg(arg,'--feature')
    elif arg.startswith('--region'):
        region = checkArg(arg,'--region')
    elif arg.startswith('--CONVERT') or arg.startswith('CONVERT'):
        runType = 'CONVERT'
    elif arg.startswith('--FILTER') or arg.startswith('FILTER'):
        runType = 'FILTER'
    elif arg.startswith('--SUBSET') or arg.startswith('SUBSET'):
        runType = 'SUBSET'
    elif arg.startswith('--STATS') or arg.startswith('STATS'):
        runType = 'STATS'
    elif arg.startswith('--PREPROCESS') or arg.startswith('PREPROCESS'):
        runType = 'PREPROCESS'
    elif arg.startswith('--MERGE-CHR') or arg.startswith('MERGE-CHR'):
        runType = 'MERGE-CHR'
    elif arg.startswith('--MERGE-MODEL') or arg.startswith('MERGE-MODEL'):
        runType = 'MERGE-MODEL'
    elif arg.startswith('--doFiltering'):
        doFiltering = checkArg(arg,'--doFiltering',True)
    elif arg.startswith('--mergeChr'):
        mergeChr = checkArg(arg,'--mergeChr',True)
    elif arg.startswith('--filterConcordance'):
        filterConcordance = checkArg(arg,'--filterConcordance',True)
    elif arg.startswith('--dirConcordance'):
        dirConcordance = checkArg(arg,'--dirConcordance')
        filterConcordance = True
    elif arg.startswith('--overlapConcordance'):
        overlapConcordance = float(checkArg(arg,'--overlapConcordance'))
    elif arg.startswith('--percConcordance'):
        percConcordance = float(checkArg(arg,'--percConcordance'))
    elif arg.startswith('--multithread'):
        multithread = checkArg(arg,'--multithread',True)
    elif arg.startswith('--threads'):
        threads = int(checkArg(arg,'--threads'))
    elif arg.startswith('--includeReads'):
        MoreQual = checkArg(arg,'--moreQuality',True)
    elif arg.startswith('--minimumPE'):
        minimumPE = float(checkArg(arg,'--minimumPE'))
    elif arg.startswith('--minimumSR'):
        minimumSR = float(checkArg(arg,'--minimumSR'))
    elif arg.startswith('--minimumMAPQ'):
        minimumMAPQ = float(checkArg(arg,'--minimumMAPQ'))
    elif arg.startswith('--calcScore'):
        calcScore = checkArg(arg,'--calcScore',True)
        if calcScore:
            filterConcordance = True
            MoreQual = True
            IncludeReads = True
    elif arg.startswith('--filterScore'):
        filterScore = float(checkArg(arg,'--filterScore'))
    elif arg.startswith('--noCols'):
        pass
    else:
        print('{colError}Error: Unknown argument {0} provided.{colReset}\n'.format(arg, **globals()),flush=True)
        sys.exit()

# Create frequently used functions
def doWriteWindows(outDat, windowStep=windowStep, doAnnotation=doAnnotation, RefFile=RefFile, windowType=windowType, progressBar=100000000, logFile=sys.stdout):
    printT('Calculating window-based statistics.', file=logFile)
    # NB: outDat should reach this point as a single chromosome chunk
    if outDat.shape[0] == 0:
        printT("No rows identified in input file '{0}'".format(outDat), file=logFile)
        return
    chrNo = outDat['Chromosome'].iloc[0]

    # Reset holders (window names and counts)
    windowStarts = []
    windowEnds = []
    windowCounts = []
    SubPopWindowCount = []
    sampleNames = []

    # iterate through windows, dynamic to bounds of chromosome
    for windowStart in range(round(int(min(outDat.Start)),-len(str(windowStep))),int(max(outDat.End))+1,windowStep):  # windows as (y, y+windowSize)

        # Print progress
        if windowStart % progressBar == 0:
            printT('Processing from base {0:,}.'.format(windowStart), file=logFile)

        # Add window counts
        windowStarts.append(str(windowStart))
        windowEnds.append(str(windowStart+windowSize))

        # [old] as variant sum
        if windowType.lower() == 'variantcount':
            windowCounts.append(sum(outDat.loc[outDat.Start < (windowStart + windowSize)].loc[outDat.End > windowStart].Count))
            sampleNames.append(pd.Series([n for n in tmpWindow['Samples'].str.split(',') for n in n]).unique())
        # [new] as population frequency
        elif windowType.lower() == 'popcount':
            tmpWindow = outDat.loc[outDat.Start < (windowStart + windowSize)].loc[outDat.End > windowStart]
            windowCounts.append(pd.Series([n for n in tmpWindow['Samples'].str.split(',') for n in n]).unique().shape[0])
            sampleNames.append(','.join(pd.Series([n for n in tmpWindow['Samples'].str.split(',') for n in n]).unique()))

    # Combine Start, End and Count lists into a dataframe, held within the holder
    outDat = pd.DataFrame.from_dict({'Chromosome':chrNo,'Start':windowStarts,'End':windowEnds,'Count':windowCounts,'Samples':sampleNames})

    # Remove windows with no variants, saves a lot of space
    outDat = outDat.loc[outDat['Count'] > 0]

    # Calculate subPop frequencies
    SubPopFreqs = {}
    SubPopCols = []
    if os.path.isfile(subPops): # for each pop, add a column of their unique frequencies within the region
        subPopInfo = pd.read_table(subPops, sep='\t')
        for popType in subPopInfo.columns[1:]:
            printT('Calculating sub-population frequencies for {}'.format(popType), file=logFile)
            currSubPop = list(set(subPopInfo[popType]))
            currSubPop.sort()
            for index, pop in enumerate(currSubPop):
                printR('Processing: {0} of {1} sub-populations.'.format(index+1,len(currSubPop)), file=logFile)
                currPop = subPopInfo['Sample'][subPopInfo[popType] == pop].tolist()
                popFreqs = [round(sum([p in currPop for p in outDat.Samples.iloc[row].split(',')])/sum(subPopInfo[popType]==pop),3) for row in range(outDat.shape[0])]
                colName = popType+'_'+pop
                SubPopFreqs[colName] = popFreqs
                SubPopCols.append(colName)
            if not multithread: print('')

    if subPops != '':
        for pop in SubPopCols: # add subPop frequencies to outDat
            outDat[pop] = SubPopFreqs[pop]
    else:
        SubPopCols = []

    outDat = outDat[['Chromosome','Start','End','Count','Samples']+SubPopCols]

    # Calculate Fst
    if len(subPops) > 0 and doFst:
        for popType in subPopInfo.columns[1:]:
            printT('Calculating Fst for {}'.format(popType), file=logFile)
            popCols = pd.Series(SubPopCols)[pd.Series(SubPopCols).str.startswith(popType)]
            outDat[popType+'_Fst'] = outDat[popCols].apply(calcFstNei,axis=1)

    if (doAnnotation):
        printT('Annotating {} windows.'.format(outDat.shape[0]), file=logFile)
        annots = []
        count = 0
        for row in outDat.itertuples():
            count += 1
            annots.append(', '.join(list(set(list(ref.loc[ref.Chromosome.astype(str)==str(row[1])].loc[ref.Start.astype(int) < int(row[3])].loc[ref.End.astype(int) > int(row[2])][refCol])))))
            if count % 10000 == 0:
                printR('Annotating window {0:,} of {1:,}.'.format(count,outDat.shape[0]), file=logFile)
        outDat['Feature'] = annots

    fileName = '{0}_{1}_{2}_windows{3}_v{4}.csv'.format(outFile,MODEL,chrNo,'_annotated' if doAnnotation else '', VERSION_NUM)
    printT('Writing window output as {0}'.format(fileName), file=logFile)
    outDat.to_csv('{0}'.format(fileName),index=False)

# Remove variants according to specific thresholds.
def doFilterVariants(variantFile, model=MODEL, minimumQuality=minimumQuality, minimumPrecision=minimumPrecision,
                        maximumPercRef=maximumPercRef, maximumPercHet=maximumPercHet, maximumPercMissing=maximumPercMissing,
                        minimumPercAlt=minimumPercAlt, removeIntergenic=removeIntergenic, percConcordance=percConcordance,
                        internalFunc=False, logFile=sys.stdout):
    printT('Filtering variants.', file=logFile)
    if isinstance(variantFile, str):
        if model == '':
            if 'INS' in variantFile:
                print('{colWarn}Warning: No argument sent to --MODEL, inferred "INS" from file name.{colReset}'.format(**globals()),flush=True,file=logFile)
                model = 'INS'
            elif 'INV' in variantFile:
                print('{colWarn}Warning: No argument sent to --MODEL, inferred "INV" from file name.{colReset}'.format(**globals()),flush=True,file=logFile)
                model = 'INV'
            elif 'DEL' in variantFile:
                print('{colWarn}Warning: No argument sent to --MODEL, inferred "DEL" from file name.{colReset}'.format(**globals()),flush=True,file=logFile)
                model = 'DEL'
            elif 'DUP' in variantFile:
                print('{colWarn}Warning: No argument sent to --MODEL, inferred "DUP" from file name.{colReset}'.format(**globals()),flush=True,file=logFile)
                model = 'DUP'
            else:
                print('{colWarn}Warning: No argument sent to --MODEL, using default placeholder "MODEL".{colReset}'.format(**globals()),flush=True,file=logFile)
                model = 'MODEL'
        if not os.path.exists(variantFile): # If given a file of filenames
            print("{colWarn}Error: Provided variantFile doesn't appear to exist.{colReset}\n".format(**globals()),flush=True,file=logFile)
            sys.exit()
    printT('Reading variant file.', file=logFile)
    filtered = pd.read_csv(variantFile, low_memory=False) if isinstance(variantFile, str) else variantFile
    printT('Preprocessing variant file.', file=logFile)
    filtered = filtered.assign(PercRef = filtered['RefCalls'] / filtered['Count'])
    filtered = filtered.assign(PercHet = filtered['HetCalls'] / filtered['Count'])
    filtered = filtered.assign(PercAlt = filtered['AltCalls'] / filtered['Count'])
    filtered = filtered.assign(PercMissing = filtered['MisCalls'] / filtered['Count'])
    outDat = filtered.copy()
    preRows = filtered.shape[0]
    printT('Pre-Filter Rows: {0:,}'.format(preRows),file=logFile)

    if minimumQuality != None:       # Remove poor quality variants
        filtered = filtered[filtered['Quality'] >= minimumQuality]
        failed = outDat[outDat['Quality'] < minimumQuality]
        stats = failed.shape[0]
        printT('{0:,} variants removed for sub-par DELLY quality scores (paired read support).'.format(stats), file=logFile)
        if stats > 0:
            failFile = 'poorQuality_{0}.log'.format(model)
            printT('Writing sub-par quality variants to {0}'.format(failFile), file=logFile)
            failed.to_csv(failFile,index=False)
    if minimumPrecision != None:     # Remove poor precision variants
        filtered = filtered[filtered['Precision'] >= minimumPrecision]
        failed = outDat[outDat['Precision'] < minimumPrecision]
        stats = failed.shape[0]
        printT('{0:,} variants removed for sub-par DELLY precision scores (split read support).'.format(stats), file=logFile)
        if stats > 0:
            failFile = 'poorPrecision_{0}.log'.format(model)
            printT('Writing sub-par precision variants to {0}'.format(failFile), file=logFile)
            failed.to_csv(failFile,index=False)
    if maximumPercRef != None:      # Remove homozygous reference calls
        filtered = filtered[filtered['PercRef'] <= maximumPercRef]
        failed = outDat[outDat['PercRef'] > maximumPercRef]
        stats = failed.shape[0]
        printT('{0:,} variants removed for excessive homozygous reference calls.'.format(stats), file=logFile)
        if stats > 0:
            failFile = 'excessiveHom_{0}.log'.format(model)
            printT('Writing excessive homozygous variants to {0}'.format(failFile), file=logFile)
            failed.to_csv(failFile,index=False)
    if maximumPercHet != None:
        if excludeDupPercHet and model == 'DUP':
            pass
        else:
            filtered = filtered[filtered['PercHet'] <= maximumPercHet]
            failed = outDat[outDat['PercHet'] > maximumPercHet]
            stats = failed.shape[0]
            printT('{0:,} variants removed for excessive heterozygous calls.'.format(stats), file=logFile)
            if stats > 0:
                failFile = 'excessiveHet_{0}.log'.format(model)
                printT('Writing excessive heterozygous variants to {0}'.format(failFile), file=logFile)
                failed.to_csv(failFile,index=False)
    if minimumPercAlt != None:      # Require homozygous alternative calls
        filtered = filtered[filtered['PercAlt'] >= minimumPercAlt]
        failed = outDat[outDat['PercAlt'] < minimumPercAlt]
        stats = failed.shape[0]
        printT('{0:,} variants removed for insufficient homozygous alternative calls.'.format(stats), file=logFile)
        if stats > 0:
            failFile = 'insufficientHom_{0}.log'.format(model)
            printT('Writing insufficient homozygous variants to {0}'.format(failFile), file=logFile)
            failed.to_csv(failFile,index=False)
    if maximumPercMissing != None:  # Remove missing calls
        filtered = filtered[filtered['PercMissing'] <= maximumPercMissing]
        failed = outDat[outDat['PercMissing'] > maximumPercMissing]
        stats = failed.shape[0]
        printT('{0:,} variants removed for excessive missing genotypes.'.format(stats), file=logFile)
        if stats > 0:
            failFile = 'excessiveMis_{0}.log'.format(model)
            printT('Writing excessive missingness variants to {0}'.format(failFile), file=logFile)
            failed.to_csv(failFile,index=False)
    if removeIntergenic:            # Remove intergenic variants
        if sum(filtered.Feature.astype(str) == 'nan') > 0:
            filtered = filtered[filtered['Feature'].astype(str) != 'nan']
            stats = sum(outDat['Feature'].astype(str) == 'nan')
        else:
            filtered = filtered[filtered['Feature'].astype(str) != '']
            stats = sum(outDat['Feature'].astype(str) == '')
        printT('-{0:,} variants removed due to being intergenic.'.format(stats), file=logFile)
    if percConcordance > 0: # Filter by concordance
        foreLength = outDat.shape[0]
        concCheck = outDat.loc[outDat.Concordance >= percConcordance]
        noConcordance = foreLength - concCheck.shape[0]
        printT('{0:,} variants removed due to insufficient concordance.'.format(noConcordance))
        if noConcordance > 0:
            outDat = outDat[outDat.Concordance >= percConcordance]
    postRows = filtered.shape[0]
    printT('Post-Filter Rows: {0:,} ({1:,} removed)'.format(postRows, preRows-postRows), file=logFile)

    if internalFunc:
        return filtered
    else:
        outputName = '{0}_{1}_ALL_variants{2}_v{3}.csv'.format('Filtered' if outFile == 'outFile' else outFile, model, '_annotated' if 'annotated' in variantFile else '', VERSION_NUM)
        printT('Writing filtered file to {0}.'.format(outputName), file=logFile)
        filtered.to_csv(outputName,index=False)

# Merge per-chromosome variant files into one file.
def doMergeVariants(variantFiles, model=MODEL,cleanup=True):
    # Automatically find local files for merging.
    if variantFiles in ['INSv','INVv','DELv','DUPv','INSw','INVw','DELw','DUPw']:
        if variantFiles[-1] == 'v':
            printT("Searching current directory for '{0}' variant files.".format(variantFiles))
            variantFiles = os.popen("ls -m *{0}*variants*.csv | sed -e 's/, /,/g' | tr -d '\n'".format(variantFiles[:3])).read()
            printT("Found {0}: {1}".format(len(variantFiles.split(',')),variantFiles))
        elif variantFiles[-1] == 'w':
            printT("Searching current directory for '{0}' window files.".format(variantFiles))
            variantFiles = os.popen("ls -m *{0}*windows*.csv | sed -e 's/, /,/g' | tr -d '\n'".format(variantFiles[:3])).read()
            printT("Found {0}: {1}".format(len(variantFiles.split(',')),variantFiles))

    if model == '':
        if 'INS' in variantFiles:
            print('{colWarn}Warning: No argument sent to --MODEL, inferred "INS" from file name.{colReset}\n'.format(**globals()),flush=True)
            model = 'INS'
        elif 'INV' in variantFiles:
            print('{colWarn}Warning: No argument sent to --MODEL, inferred "INV" from file name.{colReset}\n'.format(**globals()),flush=True)
            model = 'INV'
        elif 'DEL' in variantFiles:
            print('{colWarn}Warning: No argument sent to --MODEL, inferred "DEL" from file name.{colReset}\n'.format(**globals()),flush=True)
            model = 'DEL'
        elif 'DUP' in variantFiles:
            print('{colWarn}Warning: No argument sent to --MODEL, inferred "DUP" from file name.{colReset}\n'.format(**globals()),flush=True)
            model = 'DUP'
        else:
            print('{colWarn}Warning: No argument sent to --MODEL, using default placeholder "MODEL".{colReset}\n'.format(**globals()),flush=True)
            model = 'MODEL'
    if variantFiles == '':
        print('{colError}Error: Please supply a list of files to merge.{colReset}\n'.format(**globals()),flush=True)
        sys.exit()
    elif os.path.exists(variantFiles): # If given a file of filenames
        with open(variantFiles) as f:
            fileNames = f.read().splitlines()
    else: # If given file names
        fileNames = variantFiles.split(',')

    fileExists = [os.path.isfile(file) for file in fileNames]

    if len(fileNames) <= 1:
        print('{colError}Error: Too few files provided.{colReset}\n'.format(**globals()),flush=True)
        sys.exit()

    if len(fileExists) - sum(fileExists) > 0:
        missingFiles = [fileNames[index] for index, value in enumerate(fileExists) if value]
        print('{colError}Error: {0} files were not found. These are: {1}.{colReset}\n'.format(len(missingFiles), missingFiles, **globals()),flush=True)
        sys.exit()

    printT('Reading in variant files.')
    Merged = pd.concat([pd.read_csv(i,low_memory=False) for i in fileNames])
    if 'variants' in fileNames[0]:
        if not suppressWarnings:
            print('{colWarn}Warning: Inferring files as variant files.{colReset}'.format(**globals()), flush=True)
        variantType = '_variants'
    elif '_windows' in fileNames[0]:
        if not suppressWarnings:
            print('{colWarn}Warning: Inferring files as window files.{colReset}'.format(**globals()), flush=True)
        variantType = '_windows'
    else:
        print('{colWarn}Warning: Unable to infer if input files are for variants or windows.{colReset}'.format(**globals()), flush=True)
        variantType = ''

    outputName = '{0}_{1}_chrALL{2}{3}_v{4}.csv'.format('Merged' if outFile == 'outFile' else outFile, model, variantType, '_annotated' if 'annotated' in fileNames[0] else '', VERSION_NUM)
    printT('Sorting merged file by Chromosome then Start position')
    Merged = Merged.sort_values(by=['Chromosome','Start'])
    printT('Writing merged file to {0}.'.format(outputName))
    Merged.to_csv(outputName,index=False)
    if cleanup:
        printT('Removing per-chromosome files.')
        for f in fileNames:
            os.system('rm {}'.format(f))

def doMergeModels(variantFiles, models=MODEL, chrSubset=chrSubset):
    # Automatically find local files for merging.
    if variantFiles in ['variants','windows']:
        printT("Searching current directory for '{0}' files.".format(variantFiles[:-1]))
        variantFiles = os.popen("ls -m Merged_*{0}*.csv | sed -e 's/, /,/g' | tr -d '\n'".format(variantFiles)).read()
        printT("Found {0}: {1}".format(len(variantFiles.split(',')),variantFiles))

    # Given more than one file of the same region but by different model, return a merged version
    printT('Merging files of different models.')
    if variantFiles == '':
        print('{colError}Error: No argument sent to variantFiles.{colReset}\n'.format(**globals()))
        sys.exit()

    # Convert file paths to list, break out if only one file is provided.
    vFiles = variantFiles.split(',')
    numFiles = len(vFiles)
    if numFiles == 1:
        print('{colError}Error: Only one file provided, unable to merge.{colReset}\n'.format(**globals()), flush=True)
        sys.exit()

    # Infer chromosome if not provided
    if chrSubset == '':
        print("{colWarn}Warning: Chromosome not provided, unable to infer. Setting as 'All'.{colReset}\n".format(**globals()), flush=True)
        chrSubset = 'AllChr'

    # Infer models from file names if not given, convert either to list
    if models == '':
        print('{colWarn}Warning: No models provided, inferring from file names.{colReset}\n'.format(**globals()), flush=True)
        models = []
        for f in vFiles:
            if 'DUP' in f:
                models.append('DUP')
            elif 'DEL' in f:
                models.append('DEL')
            elif 'INS' in f:
                models.append('INS')
            elif 'INV' in f:
                models.append('INV')
            else:
                print("{colError}Error: Could not infer model from '{0}'. Please supply models with --MODEL.{colReset}\n".format(f, **globals()), flush=True)
                sys.exit()
    else:
        models = models.split(',')

    # Warn if duplicate models are provided
    if len(models) != len(set(models)):
        print('{colWarn}Warning: Duplicate models supplied.{colReset}\n'.format(**globals()))
    else:
        numModels = len(models)
        if numModels != numFiles:
            print('{colError}Error: {0} model/s given, but {1} file/s provided.{colReset}\n'.format(numModels, numFiles, **globals()))
            sys.exit()
    if len(models) <= 1:
        print('{colWarn}Warning: Nonsensical to merge models, only one model present.{colReset}'.format(**globals()), flush=True)
        return

    # Actually merge the files
    for i, f in enumerate(vFiles):
        currentFile = pd.read_csv(f, low_memory=False)
        currentFile['Model'] = models[i]
        if 'merged' not in locals():
            merged = currentFile
        else:
            merged = pd.concat([merged, currentFile])

    if 'windows' in vFiles[0]:
        variantType = '_windows'
    elif 'variants' in vFiles[0]:
        variantType = '_variants'
    else:
        variantType = ''
    annotatedCheck = '_annotated' if 'annotated' in vFiles[0] else ''

    outputName = 'AllModels_{3}{0}{1}_v{2}.csv'.format(variantType,annotatedCheck,VERSION_NUM,chrSubset)
    printT('Writing model merged file to {0}.'.format(outputName))
    merged.to_csv(outputName,index=False)

def getSubset(variantFile, region=None, feature=None):
    # Given a variant file and some form of subset (gene or region) return stats
    if region != None and feature != None:
        print('{colError}Error: Both a region and feature supplied. Please request separately.{colReset}\n'.format(**globals()),flush=True)
        sys.exit()

    if not os.path.isfile(variantFile):
        print("{colError}Error: Provided variantFile doesn't seem to exist.{colReset}\n".format(**globals()),flush=True)
        sys.exit()

    printT('Reading in variant file: {0}.'.format(variantFile))
    variantFile = pd.read_csv(variantFile)

    if feature != None:
        if 'Feature' not in variantFile.columns:
            print("{colError}Error: User requested subset by Feature but variant file is not annotated.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
        else:
            printT('Subsetting to {0}.'.format(feature))
            variantFile = variantFile.ix[variantFile['Feature'].astype(str).str.contains(feature)]

    if region != None:
        # Format should be chr:bpA-bpB
        try:
            chromosome = region.split(':')[0]
            bpA = region.split(':')[1].split('-')[0]
            bpB = region.split(':')[1].split('-')[1]
        except:
            print("{colError}Error: Unable to parse provided region. Please format as 'chromosome:basepairA-basepairB'.{colReset}\n".format(**globals()),flush=True)
            sys.exit()
        if chromosome not in variantFile['Chromosome'].values:
            print("{colError}Error: Provided chromosome '{0}' not present in variant file.{colReset}\n".format(chromosome, **globals),flush=True)
            sys.exit()

        printT('Subsetting to {0}.'.format(region))
        variantFile = variantFile.loc[(variantFile['Chromosome'] == chromosome) & (variantFile['Start'] < int(bpB)) & (variantFile['End'] > int(bpA))]

    variantFile = variantFile.sort_values(by='Count', ascending=False)

    printT('Subset successful.')
    print('{0:,} variants present.'.format(variantFile.shape[0]))
    if 'Model' in variantFile.columns:
        print('DEL:{0:,}, DUP:{1:,}, INS:{2:,}, INV:{3:,}'.format(sum(variantFile['Model']=='DEL'), sum(variantFile['Model']=='DUP'), sum(variantFile['Model']=='INS'), sum(variantFile['Model']=='INV')))
    # print('Mean variant length: {0:,}'.format(variantFile['Length'].mean()))
    # print('Median variant length: {0:,}'.format(variantFile['Length'].median()))
    # print('Variant Range: {0:,} to {1:,}.\n'.format(variantFile['Length'].min(), variantFile['Length'].max()))

    outputName = '{0}_{1}_v{2}.csv'.format('Subset' if outFile == 'outFile' else outFile, feature if feature is not None else region, VERSION_NUM)
    printT('Writing subset to {0}.'.format(outputName))
    variantFile.to_csv(outputName,index=False)

def prepForVisualisation(filePrefix):
    printT("Processing files prefixed '{0}' for visualisation.".format(filePrefix))

    # Create output directory
    outDirName = './SVPop_Files'
    os.makedirs(outDirName, exist_ok=True)

    filePrefix = filePrefix.rstrip('_')+'_' # Ensure prefix ends in _, without adding a double

    for model in ['DEL','DUP','INS','INV']:
        printT('Processing {0}.'.format(model))

        # Existing Files
        varFile = filePrefix+model+'_chrALL_variants_annotated_v'+VERSION_NUM+'.csv'
        winFile  = filePrefix+model+'_chrALL_windows_annotated_v' +VERSION_NUM+'.csv'

        # New File Names
        AllIndexName  = '{0}/{1}_AllIndex.csv'.format(outDirName, model)
        FreqIndexName = '{0}/{1}_FrqIndex.csv'.format(outDirName, model)
        VariantsName  = '{0}/{1}_Variants.csv'.format(outDirName, model)
        WindowsName   = '{0}/{1}_Windows.csv'.format(outDirName, model)

        printT('Reading in variant and window files.')
        variants = pd.read_csv(varFile)
        windows  = pd.read_csv(winFile)

        # Full Files
        printT('Writing output files to {0}/.'.format(outDirName))
        variants.to_csv(VariantsName,index=False)                                                             # All Variants
        windows.to_csv(WindowsName,index=False)                                                               # All Windows
        variants[['Chromosome','Start','End']].to_csv(AllIndexName,index=False)                               # All Variants Index
        variants[variants.Frequency >= 0.05][['Chromosome','Start','End']].to_csv(FreqIndexName,index=False)  # Freq Variants Index

def calcFstNei(values):
    # Given an array of variant frequencies, calculate the Nei's Fst
    if False not in [np.isnan(val) for val in values]:
        return np.nan
    else:
        A = np.array(values)
        Hs = np.nansum(2*A*(1-A)) / len(A)
        Ht = 2 * np.nanmean(A) * np.nanmean(1-A)
        if Ht == 0:
            return(np.nan)
        return(round(1 - (Hs / Ht),3))

def simpleLog(chrChunk, SampleID, stat, statName, logfile):
    # Given basic info, ensure that a simple log file is kept
    if not logfile.endswith('.log'):
        logfile += '.log'
    if not os.path.isfile(logfile):
        with open(logfile, 'w') as f:
            f.write('Chromosome,Sample,{0}\n'.format(statName))
    with open(logfile, 'a') as f:
        f.write('{0},{1},{2}\n'.format(chrChunk, SampleID, stat))

def analyseChr(chrChunk):
    printT('Conducting analysis for chromosome {0}.'.format(chrChunk), file=sys.stdout)
    with open('{0}_{1}_{2}.log'.format(outFile, MODEL, chrChunk), 'a') as f:
        printT('Conducting analysis for chromosome {0}.'.format(chrChunk), file=f)

        # Read in vcf files, clean up for stats
        printT('Reading in structural variants vcf file/s for chromosome {0}.'.format(chrChunk), file=f)
        outDat = pd.DataFrame() # merge holder
        skippedFiles = []
        skippedCount = 0
        num = 0
        hNames = ['Chromosome','Start','Name','X','Type','X2','Quality','Info','Format','Details']
        for SampleID in samples:
            # Processing count
            num += 1
            if num % 500 == 0:
                printR('Processing sample {0} of {1}.'.format(num,len(samples)), file=f)

            # Check file exists before reading
            variantsExist = os.path.isfile(SampleID)
            if filterConcordance and MODEL in ['DEL','DUP']:
                concordanceExist = os.path.isfile(dirConcordance+SampleID.lstrip('.').partition('.')[0].split('/')[-1]+'.cnvs')
            else:
                concordanceExist = True

            if variantsExist and concordanceExist:
                # Read in each sample
                dat = pd.read_table(SampleID,comment='#',header=None,names=hNames,
                    dtype={'Chromosome':str,'Start':int,'Name':str,'X':str,'Type':str,'X2':str,'Quality':str,'Info':str,'Format':str,'Details':str},
                    usecols=['Chromosome','Start','Name','Type','Quality','Info','Format','Details'])

                # Subset to chromosome
                dat = dat.loc[dat['Chromosome'].astype(str)==str(chrChunk)].reset_index()

                if (dat.shape[0] == 0): # Check that the chromosome subset worked.
                    if not suppressWarnings:
                        print('Warning: No variants found in "{0}" for "{1}".'.format(chrChunk, SampleID),flush=True)
                    skippedCount += 1
                    skippedFiles.append(SampleID+' ('+chrChunk+')')
                else:
                    # Clean to vitals
                    dat = dat.assign(End=dat.Info.str.partition('END=')[2].str.partition(';')[0])
                    dat = dat.assign(Precision=dat.Info.str.partition(';')[0])
                    dat = dat.assign(Samples=SampleID.partition('.')[0].split('/')[-1]) # remove file suffix and directories

                    # Pull raw read counts
                    if IncludeReads:
                        dat = dat.assign(RefPairs=dat.Details.str.split(':').str[dat.Format.iloc[0].split(':').index('DR')])
                        dat = dat.assign(AltPairs=dat.Details.str.split(':').str[dat.Format.iloc[0].split(':').index('DV')])
                        dat = dat.assign(RefJunct=dat.Details.str.split(':').str[dat.Format.iloc[0].split(':').index('RR')])
                        dat = dat.assign(AltJunct=dat.Details.str.split(':').str[dat.Format.iloc[0].split(':').index('RV')])

                    # Additional map stats
                    if MoreQual:
                        dat = dat.assign(PE=dat.Info.str.partition(';PE=')[2].str.partition(';')[0])        # Num. supporting PE reads
                        dat = dat.assign(SR=dat.Info.str.partition('SR=')[2].str.partition(';')[0])         # Num. supporting SR reads
                        dat = dat.assign(MapQual=dat.Info.str.partition('MAPQ=')[2].str.partition(';')[0])  # Median mapping quality

                    # Include phasing values
                    if PullPhasing:
                        dat = dat.assign(Phase=dat.Details.str.split(':').str[dat.Format.iloc[0].split(':').index('GT')])

                    # Remove variants with a sub-par SR, PE or MapQ score (nb. this is a hard on variant filter, not a pop-based stat)
                    if minimumPE > 0:
                        belowPE = dat.loc[dat.PE.astype(int) < minimumPE].shape[0]
                        dat = dat.loc[dat.PE.astype(int) >= minimumPE]
                        simpleLog(chrChunk, SampleID.partition('.')[0].split('/')[-1], belowPE, 'SubParPE', 'minimumPE_{0}_{1}'.format(MODEL, chrChunk))
                    if minimumSR > 0:
                        dat.SR.replace('', 0, inplace=True)
                        belowSR = dat.loc[dat.SR.astype(int) < minimumSR].shape[0]
                        dat = dat.loc[dat.SR.astype(int) >= minimumSR]
                        simpleLog(chrChunk, SampleID.partition('.')[0].split('/')[-1], belowSR, 'SubParSR', 'minimumSR_{0}_{1}'.format(MODEL, chrChunk))
                    if minimumMAPQ > 0:
                        belowMAPQ = dat.loc[dat.MAPQ.astype(int) < minimumMAPQ].shape[0]
                        dat = dat.loc[dat.MAPQ.astype(int) >= minimumMAPQ]
                        simpleLog(chrChunk, SampleID.partition('.')[0].split('/')[-1], belowMAPQ, 'SubParMAPQ', 'minimumMAPQ_{0}_{1}'.format(MODEL, chrChunk))

                    # Filter out variants not present in secondary discovery method
                    if filterConcordance and MODEL in ['DEL','DUP']:
                        # Read in concordance dataset and subset to relevant SV type
                        refConcord = pd.read_csv(dirConcordance+SampleID.lstrip('.').partition('.')[0].split('/')[-1]+'.cnvs')
                        refConcord = refConcord[refConcord['Type'] == 'DEL'] if MODEL == 'DEL' else refConcord[refConcord['Type'] == 'DUP']

                        concordanceLog = []
                        if not refConcord.shape[0] == 0:
                            # Verify variants against the concordance dataset
                            for indexD, row_dat in dat.iterrows():
                                verifiedByConcordance = False
                                # perform check
                                for indexC, row_con in refConcord.iterrows():
                                    # Check for overlap
                                    if (int(row_dat['Start']) <= row_con['End']) and (row_con['Start'] <= int(row_dat['End'])):
                                        overlapSize = min(int(row_dat['End']), row_con['End']) - max(int(row_dat['Start']), row_con['Start'])
                                        overlapProp = overlapSize / (int(row_dat['End'])-int(row_dat['Start'])) # Filter as proportion of delly variant, as cnvnator has bin_size resolution
                                        if overlapProp >= overlapConcordance:
                                            #print(row_dat)
                                            verifiedByConcordance = True
                                            break # Stop checking variant if verified.
                                if verifiedByConcordance:
                                    concordanceLog.append(True)
                                else:
                                    concordanceLog.append(False)

                            # Filter down to only verified variants
                            if not quietConcordance:
                                printT('{0} of {1} variants were verified ({2}%, {3}).'.format(sum(concordanceLog), len(concordanceLog), round(100*sum(concordanceLog)/len(concordanceLog),2), SampleID.lstrip('.').partition('.')[0].split('/')[-1]), file=f)
                            if percConcordance == 1:
                                dat = dat.loc[concordanceLog]
                            dat = dat.assign(Concordance=[int(x) for x in concordanceLog])
                        else:
                            if not quietConcordance:
                                printT('No variants present for verification. ({0})'.format(SampleID.partition('.')[0].split('/')[-1]), file=f)
                            dat = dat.assign(Concordance=0)
                            dat = dat.loc[[False]*dat.shape[0]]

                        with open('concordanceLog_{0}_{1}.log'.format(MODEL,chrChunk),'a') as cLog:
                            if os.stat('concordanceLog_{0}_{1}.log'.format(MODEL,chrChunk)).st_size == 0:
                                cLog.write('Sample,Chromosome,Total,Verified,Percentage\n')
                            cLog.write('{0},{1},{2},{3},{4}\n'.format(SampleID.lstrip('.').partition('.')[0].split('/')[-1], chrChunk, len(concordanceLog), sum(concordanceLog), round(100*sum(concordanceLog)/len(concordanceLog),2) if len(concordanceLog) else 'inf'))

                    # Location is for merging, split later
                    dat = dat.assign(Location=dat.Chromosome.astype(str) + '-' + dat.Start.astype(str) + '-' + dat.End.astype(str))

                    # Pull length here if model is INS
                    if MODEL == 'INS':
                        dat = dat.assign(Length=dat.Info.str.partition('INSLEN=')[2].str.partition(';')[0])
                        tmpCols = ['Chromosome','Start','End','Type','Quality','Precision','Location','Samples','Length','Phase']+readCols+qualCols
                    else:
                        tmpCols = ['Chromosome','Start','End','Type','Quality','Precision','Location','Samples','Phase']+readCols+qualCols
                    dat = dat[tmpCols]

                    # Merge current sample into total sample, have quality and precision (and read counts) as added columns
                    if sum(outDat.shape) == 0:
                        outDat = dat
                    else:
                        outDat = outDat.merge(dat,on='Location',how='outer')
                        outDat = outDat.assign(Type=MODEL)
                        outDat = outDat.assign(Samples=outDat['Samples_x'].astype(str) + ',' + outDat['Samples_y'].astype(str))
                        outDat = outDat.assign(Quality=outDat['Quality_x'].astype(str) + ',' + outDat['Quality_y'].astype(str))
                        outDat = outDat.assign(Precision=outDat['Precision_x'].astype(str) + ',' + outDat['Precision_y'].astype(str))
                        if IncludeReads:
                            outDat = outDat.assign(RefPairs=outDat['RefPairs_x'].astype(str) + ',' + outDat['RefPairs_y'].astype(str))
                            outDat = outDat.assign(AltPairs=outDat['AltPairs_x'].astype(str) + ',' + outDat['AltPairs_y'].astype(str))
                            outDat = outDat.assign(RefJunct=outDat['RefJunct_x'].astype(str) + ',' + outDat['RefJunct_y'].astype(str))
                            outDat = outDat.assign(AltJunct=outDat['AltJunct_x'].astype(str) + ',' + outDat['AltJunct_y'].astype(str))
                        if MoreQual:
                            outDat = outDat.assign(PE=outDat['PE_x'].astype(str) + ',' + outDat['PE_y'].astype(str))
                            outDat = outDat.assign(SR=outDat['SR_x'].astype(str) + ',' + outDat['SR_y'].astype(str))
                            outDat = outDat.assign(MapQual=outDat['MapQual_x'].astype(str) + ',' + outDat['MapQual_y'].astype(str))
                        if PullPhasing:
                            outDat = outDat.assign(Phase=outDat['Phase_x'].astype(str) + ',' + outDat['Phase_y'].astype(str))
                        if filterConcordance:
                            outDat = outDat.assign(Concordance=outDat['Concordance_x'].astype(str) + ',' + outDat['Concordance_y'].astype(str))
                        if MODEL == 'INS': # Store INSLEN as per-sample, currently not distinguishing between insertions of different length
                            outDat = outDat.assign(Length=outDat['Length_x'].astype(str) + ',' + outDat['Length_y'].astype(str))
                            outDat = outDat[['Location','Type','Quality','Precision','Samples','Length','Phase']+readCols+qualCols]
                        else:
                            outDat = outDat[['Location','Type','Quality','Precision','Samples','Phase']+readCols+qualCols]
            else:
                if suppressWarnings == False:
                    if not concordanceExist:
                        print('Warning: No concordance file identified for "{0}".'.format(SampleID), flush=True, file=f)
                    elif not variantsExist:
                        print('Warning: No variants identified in chromosome {0} for "{1}".'.format(chrChunk,SampleID), flush=True, file=f)
                    if filterConcordance and not concordanceExist:
                        print('Warning: No concordance file present for "{0}".'.format(SampleID), flush=True, file=f)
                skippedCount += 1
                skippedFiles.append(SampleID+' (All)')
                samples.remove(SampleID)    # Re-align frequency as percentage of samples parsed, not samples given
            gc.collect()

        # Informing user regarding missed files.
        printT("{0} file/s could not be located.".format(skippedCount), file=f)
        if skippedCount > 0:
            printT("Writing skipped file/s to skippedFiles_{0}_{1}.log".format(MODEL,chrChunk), file=f)
            with open('skippedFiles_{0}_{1}.log'.format(MODEL,chrChunk),'a') as skipLog:
                for item in skippedFiles:
                    skipLog.write("{0}\n".format(item))

        # Check if whole chromosome was empty. If so, skip to next.
        if (skippedCount >= len(samples)):
            printT('No variants found in {0}, skipping chromosome.'.format(chrChunk), file=f)
        else:
            # Clean nan's from Samples, Precision and Quality (and Length and Reads)
            printT('Removing NA calls.', file=f)
            outDat['Samples'] = outDat.Samples.str.replace(',nan,',',')
            outDat['Samples'] = outDat.Samples.str.replace('nan,','')
            outDat['Samples'] = outDat.Samples.str.replace(',nan','')
            outDat['Precision'] = outDat.Precision.str.replace(',nan,',',')
            outDat['Precision'] = outDat.Precision.str.replace('nan,','')
            outDat['Precision'] = outDat.Precision.str.replace(',nan','')
            outDat['Quality'] = outDat.Quality.str.replace(',nan,',',')
            outDat['Quality'] = outDat.Quality.str.replace('nan,','')
            outDat['Quality'] = outDat.Quality.str.replace(',nan','')
            if MODEL == 'INS':
                outDat['Length'] = outDat.Length.str.replace(',nan,',',')
                outDat['Length'] = outDat.Length.str.replace('nan,','')
                outDat['Length'] = outDat.Length.str.replace(',nan','')
            if IncludeReads:
                outDat['RefPairs'] = outDat.RefPairs.str.replace(',nan,',',')
                outDat['RefPairs'] = outDat.RefPairs.str.replace('nan,','')
                outDat['RefPairs'] = outDat.RefPairs.str.replace(',nan','')
                outDat['AltPairs'] = outDat.AltPairs.str.replace(',nan,',',')
                outDat['AltPairs'] = outDat.AltPairs.str.replace('nan,','')
                outDat['AltPairs'] = outDat.AltPairs.str.replace(',nan','')
                outDat['RefJunct'] = outDat.RefJunct.str.replace(',nan,',',')
                outDat['RefJunct'] = outDat.RefJunct.str.replace('nan,','')
                outDat['RefJunct'] = outDat.RefJunct.str.replace(',nan','')
                outDat['AltJunct'] = outDat.AltJunct.str.replace(',nan,',',')
                outDat['AltJunct'] = outDat.AltJunct.str.replace('nan,','')
                outDat['AltJunct'] = outDat.AltJunct.str.replace(',nan','')
            if MoreQual:
                outDat['SR'] = outDat.SR.str.replace(',nan,',',')
                outDat['SR'] = outDat.SR.str.replace('nan,','')
                outDat['SR'] = outDat.SR.str.replace(',nan','')
                outDat['PE'] = outDat.PE.str.replace(',nan,',',')
                outDat['PE'] = outDat.PE.str.replace('nan,','')
                outDat['PE'] = outDat.PE.str.replace(',nan','')
                outDat['MapQual'] = outDat.MapQual.str.replace(',nan,',',')
                outDat['MapQual'] = outDat.MapQual.str.replace('nan,','')
                outDat['MapQual'] = outDat.MapQual.str.replace(',nan','')
            if PullPhasing:
                outDat['Phase'] = outDat.Phase.str.replace(',nan,',',')
                outDat['Phase'] = outDat.Phase.str.replace('nan,','')
                outDat['Phase'] = outDat.Phase.str.replace(',nan','')
            if filterConcordance:
                outDat['Concordance'] = outDat.Concordance.str.replace(',nan,',',')
                outDat['Concordance'] = outDat.Concordance.str.replace('nan,','')
                outDat['Concordance'] = outDat.Concordance.str.replace(',nan','')

            # Pull Chr, Start and End out of Location
            printT('Properly formatting genomic locations.', file=f)
            Locs = pd.DataFrame(outDat.Location.str.split('-').tolist(),columns=['Chromosome','Start','End'])
            outDat['Chromosome'] = Locs['Chromosome']
            outDat['Start'] = pd.to_numeric(Locs['Start'])
            outDat['End'] = pd.to_numeric(Locs['End'])
            if MODEL != 'INS': # Only for non-INS
                outDat['Length'] = (outDat.End.astype(int) - outDat.Start.astype(int))

            if MoreQual:
                # Longer reads with poor PE support tend to be false, removing.
                if doFiltering:
                    outDat = outDat.loc[-((outDat.Length >= 500) & (outDat.PE == 0))]

            outDat = outDat[['Chromosome','Start','End','Length','Type','Quality','Precision']+readCols+qualCols+['Samples','Phase']]

            # Filter out variants which overlap with assembly gaps
            if filterGaps:
                printT('Filtering out variants which cover known assembly gaps.', file=f)
                gapsChunk = gaps.loc[gaps.Chromosome.astype(str) == chrChunk]
                gapVariantCount = 0
                for row in gapsChunk.itertuples():
                    tmp = outDat.loc[outDat.Start.astype(int) <= int(row[3])].loc[outDat.End.astype(int) >= int(row[2])].index
                    gapVariantCount += len(tmp)
                    # if gapVariantCount > 0:
                    #     gapOverlapFile = 'gapOverlap_'+chrChunk'.txt'
                    #     printT('Writing gap overlap variants to {0}.'.format(gapOverlapFile))
                    #     outDat.iloc[tmp].to_csv(gapOverlapFile)
                    outDat.drop(list(tmp),inplace=True)
                printT('{0:,} variants removed from chromosome {1} due to assembly gap overlap.'.format(gapVariantCount,chrChunk), file=f)

            outDat = outDat.sort_values(by=['Chromosome','Start']) # Sort by start position

            SampleCount, SampleFrequency, QualityCount, PrecisionCount = ([],[],[],[])
            if MODEL == 'INS':
                LengthMedian = []
            if IncludeReads:
                RefPairsMedian, AltPairsMedian, RefJunctMedian, AltJunctMedian = ([],[],[],[])
            if MoreQual:
                splitReadsMedian, pairedReadsMedian, mappingQualsMedian = ([], [], [])
            if PullPhasing:
                RefCount, HetCount, AltCount, MisCount = ([],[],[],[])
            if filterConcordance:
                meanConcordance = []

            printT('Calculating variant-based statistics.', file=f)
            for row in outDat.itertuples():
                sampleCell = row[(list(outDat.columns).index('Samples')+1)].split(',')
                qualityCell = row[(list(outDat.columns).index('Quality')+1)].split(',')
                precisionCell = row[(list(outDat.columns).index('Precision')+1)].split(',')

                SampleCount.append(len(sampleCell))
                SampleFrequency.append(len(sampleCell)/len(samples))                        # Use for grabbing subPop frequencies
                QualityCount.append(qualityCell.count('PASS')/len(qualityCell))             # Quality as percentage 'PASS'
                PrecisionCount.append(precisionCell.count('PRECISE')/len(precisionCell))    # Precision as percentage 'PRECISE'

                if IncludeReads:
                    # Split per-variant read count pseudo-list, make true list
                    refPairs = row[(list(outDat.columns).index('RefPairs')+1)].split(',')
                    altPairs = row[(list(outDat.columns).index('AltPairs')+1)].split(',')
                    refJunct = row[(list(outDat.columns).index('RefJunct')+1)].split(',')
                    altJunct = row[(list(outDat.columns).index('AltJunct')+1)].split(',')

                    # Grab median of read counts
                    RefPairsMedian.append(int(pd.Series(refPairs).median()))
                    AltPairsMedian.append(int(pd.Series(altPairs).median()))
                    RefJunctMedian.append(int(pd.Series(refJunct).median()))
                    AltJunctMedian.append(int(pd.Series(altJunct).median()))

                if MoreQual:
                    splitReads = [x for x in row[(list(outDat.columns).index('SR')+1)].split(',') if x != '']
                    pairedEnds = row[(list(outDat.columns).index('PE')+1)].split(',')
                    mappingQuals = row[(list(outDat.columns).index('MapQual')+1)].split(',')

                    splitReadsMedian.append(int(pd.Series(splitReads).median()) if splitReads != [] else 0)
                    pairedReadsMedian.append(int(pd.Series(pairedEnds).median()))
                    mappingQualsMedian.append(int(pd.Series(mappingQuals).median()))

                if PullPhasing:
                    try:
                        RefCount.append(pd.Series(row[(list(outDat.columns).index('Phase')+1)].split(',')).value_counts()['0/0'])
                    except KeyError:
                        RefCount.append(0)
                    try:
                        HetCount.append(pd.Series(row[(list(outDat.columns).index('Phase')+1)].split(',')).value_counts()['0/1'])
                    except KeyError:
                        HetCount.append(0)
                    try:
                        AltCount.append(pd.Series(row[(list(outDat.columns).index('Phase')+1)].split(',')).value_counts()['1/1'])
                    except KeyError:
                        AltCount.append(0)
                    try:
                        MisCount.append(pd.Series(row[(list(outDat.columns).index('Phase')+1)].split(',')).value_counts()['./.'])
                    except KeyError:
                        MisCount.append(0)

                if filterConcordance:
                    concordanceCell = [float(x) for x in row[(list(outDat.columns).index('Concordance')+1)].split(',')]
                    meanConcordance.append(np.mean(concordanceCell))

                if MODEL == 'INS': # Calculate median insertion length if INS
                    lengthCell = row[(list(outDat.columns).index('Length')+1)].split(',')
                    LengthMedian.append(int(pd.Series(lengthCell).median()))

            # Get sub pop frequencies
            SubPopFreqs = {}
            SubPopCols = []
            if len(subPops) > 0:
                for popType in subPopInfo.columns[1:]:
                    printT('Calculating sub-populations frequencies for {}'.format(popType), file=f)
                    currSubPop = list(set(subPopInfo[popType]))
                    currSubPop.sort()
                    for index, pop in enumerate(currSubPop):
                        nPop = sum(subPopInfo[popType]==pop)
                        printR('Processing: {0} of {1} sub-populations.'.format(index+1,len(currSubPop)), file=f)
                        currPop = subPopInfo['Sample'][subPopInfo[popType] == pop].tolist()
                        #popCounts = [sum([p in currPop for p in outDat.Samples[row].split(',')]) for row in range(outDat.shape[0])]
                        popFreqs = [round(sum([p in currPop for p in outDat.Samples.iloc[row].split(',')])/nPop,3) for row in range(outDat.shape[0])]
                        colName = popType+'_'+pop
                        SubPopFreqs[colName] = popFreqs
                        SubPopCols.append(colName)
                    if not multithread: print('')

            outDat['Count'] = SampleCount
            outDat['Frequency'] = SampleFrequency
            outDat['Quality'] = QualityCount
            outDat['Precision'] = PrecisionCount
            if IncludeReads:
                outDat['RefPairs'] = RefPairsMedian
                outDat['AltPairs'] = AltPairsMedian
                outDat['RefJunct'] = RefJunctMedian
                outDat['AltJunct'] = AltJunctMedian
            if MoreQual:
                outDat['SR'] = splitReadsMedian
                outDat['PE'] = pairedReadsMedian
                outDat['MapQual'] = mappingQualsMedian
            if PullPhasing:
                outDat['RefCalls'] = RefCount
                outDat['HetCalls'] = HetCount
                outDat['AltCalls'] = AltCount
                outDat['MisCalls'] = MisCount
            if filterConcordance:
                outDat['Concordance'] = meanConcordance
            if MODEL == 'INS':
                outDat['Length'] = LengthMedian
            for subPop in SubPopFreqs:
                outDat[subPop] = SubPopFreqs[subPop]

            keptColumns = ['Chromosome','Start','End','Length','Count','Frequency','Quality','Precision','Samples']+readCols+qualCols+['Phase','RefCalls','HetCalls','AltCalls','MisCalls']+SubPopCols

            # Calculate Fst
            if len(subPops) > 0 and doFst:
                for popType in subPopInfo.columns[1:]:
                    printT('Calculating Fst for {}'.format(popType), file=f)
                    popCols = pd.Series(SubPopCols)[pd.Series(SubPopCols).str.startswith(popType)]
                    outDat[popType+'_Fst'] = outDat[popCols].apply(calcFstNei,axis=1)
                    keptColumns.append(popType+'_Fst')

            outDat = outDat[keptColumns]
            outDat.columns = keptColumns

            # Remove super-short variants
            foreLength = outDat.shape[0]
            minCheck = outDat.loc[outDat.Length > minLength]   # indicated by minLength variable
            underMinLength = foreLength - minCheck.shape[0]
            printT('{0:,} variants removed from chromosome {1} due to exceeding minLength.'.format(underMinLength,chrChunk), file=f)
            if underMinLength > 0:
                underMinFile = 'underMinLength_{0}_{1}.log'.format(MODEL,chrChunk)
                printT('Writing underMinLength variants to {0}.'.format(underMinFile), file=f)
                outDat.loc[outDat.Length <= minLength].to_csv(underMinFile)   # indicated by minLength variable
                outDat = minCheck

            # Remove super-long variants
            foreLength = outDat.shape[0]
            maxCheck = outDat.loc[outDat.Length < maxLength]   # indicated by maxLength variable
            overMaxLength = foreLength - maxCheck.shape[0]
            printT('{0:,} variants removed from chromosome {1} due to exceeding maxLength.'.format(overMaxLength,chrChunk), file=f)
            if overMaxLength > 0:
                overMaxFile = 'overMaxLength_{0}_{1}.log'.format(MODEL,chrChunk)
                printT('Writing overMaxLength variants to {0}.'.format(overMaxFile), file=f)
                outDat.loc[outDat.Length >= maxLength].to_csv(overMaxFile)   # indicated by maxLength variable
                outDat = maxCheck

            # Filtering step if not removing intergenic (faster, as we only annotate post-filter variants)
            if doFiltering and not removeIntergenic:
                outDat = doFilterVariants(outDat, model=MODEL, minimumQuality=minimumQuality, minimumPrecision=minimumPrecision,
                    maximumPercRef=maximumPercRef, maximumPercHet=maximumPercHet, minimumPercAlt=minimumPercAlt,
                    maximumPercMissing=maximumPercMissing, removeIntergenic=removeIntergenic, internalFunc=True, logFile=f)

            # Annotate variants
            if doAnnotation and writeVariants:
                printT('Annotating {} variants.'.format(outDat.shape[0]), file=f)
                annots = []
                count = 0
                for row in outDat.itertuples():
                    count += 1
                    annots.append(', '.join(list(set(list(ref.loc[ref.Chromosome.astype(str)==str(row[1])].loc[ref.Start.astype(int) < int(row[3])].loc[ref.End.astype(int) > int(row[2])][refCol])))))
                    if count % 10000 == 0:
                        printR('Annotating variant {0:,} of {1:,}.'.format(count,outDat.shape[0]), file=f)
                outDat['Feature'] = annots                
            if not writeSamples:
                outDat.drop('Samples',axis=1).to_csv(fileName,index=False)

            # Filtering step if removing intergenic (slower, as we need to annotation all variants)
            if doFiltering and removeIntergenic:
                outDat = doFilterVariants(outDat, model=MODEL, minimumQuality=minimumQuality, minimumPrecision=minimumPrecision,
                    maximumPercRef=maximumPercRef, maximumPercHet=maximumPercHet, minimumPercAlt=minimumPercAlt,
                    maximumPercMissing=maximumPercMissing, removeIntergenic=removeIntergenic, filterConcordance=filterConcordance,
                    percConcordance=percConcordance, internalFunc=True, logFile=f)

            # Calculate SVPop scores for each variant, filter if requested
            if calcScore:
                reqColumns = ['Concordance', 'PercAlt', 'PercHet', 'SR', 'Frequency']
                reqCheck = list(compress(reqColumns,[x not in outDat.columns for x in reqColumns]))
                if len(reqCheck) > 0:
                    printT('Unable to calculate score due to missing columns: {0}'.format(reqCheck), file=f)
                else:
                    # Calculate score components
                    outDat['Score_Calls'] = outDat['PercAlt'] + (outDat['PercHet'] * 0.5)
                    outDat['Score_MapQ'] = (outDat['MapQual'] / 60)
                    outDat['Score_SR'] = (outDat['SR'] / 10)

                    # Calculate score - the key bit
                    outDat['Score'] = (outDat['Score_Calls'] + outDat['Score_MapQ'] + outDat['Score_SR'] + outDat['Frequency'] + outDat['Concordance']) / 5

                    # Filter by score if required
                    if filterScore > 0 and filterScore < 1: # Nb. filterScore as False evaluates numerically as 0, so this defaults to False
                        foreLength = outDat.shape[0]
                        scoreCheck = outDat.loc[outDat.Score >= filterScore]
                        poorScore = foreLength - scoreCheck.shape[0]
                        printT('{0:,} variants removed from chromosome {1} due to insufficient score.'.format(poorScore,chrChunk), file=f)
                        if poorScore > 0:
                            outDat = outDat[outDat.Score < filterScore]

                    # Remove component columns
                    outDat.drop(['Score_Calls','Score_MapQ','Score_SR'],axis=1,inplace=True)

            # Writing variant files out
            if writeVariants:
                fileName = '{0}_{1}_{2}_variants{3}_v{4}.csv'.format(outFile,MODEL,chrChunk,'_annotated' if doAnnotation else '',VERSION_NUM)
                printT('Writing variant output as {0}'.format(fileName), file=f)
                outDat.to_csv(fileName,index=False)

            # Write out windows files
            if writeWindows and outDat.shape[0] > 0:
                printT('Writing window output for {0}'.format(chrChunk), file=f)
                doWriteWindows(outDat=outDat,windowStep=windowStep,doAnnotation=doAnnotation,windowType=windowType, logFile=f)

def runMain():
    global readCols
    global qualCols
    readCols = ['RefPairs','AltPairs','RefJunct','AltJunct'] if IncludeReads else []
    qualCols = ['MapQual','PE','SR'] if MoreQual else []
    if filterConcordance: readCols.append('Concordance')

    # Check required arguments were provided.
    if len(reqArgs) > 0:
        print('{colError}Error: Missing required arguments: '+', '.join(reqArgs)+'.{colReset}\n'.format(**globals()),flush=True)
        sys.exit()
    if True not in [writeVariants,writeWindows]:
        print('{colError}Error: Given arguments will result in no output. Set --writeVariants and/or --writeWindows to True.{colReset}\n'.format(**globals()),flush=True)
        sys.exit()

    # Argument confirmation to user.
    printT('Starting Main Analysis.')
    print('\n{colTime}Input File:{colReset} {}'.format(inFile, **globals()),flush=True)
    print('{} samples identified.\n'.format(len(samples)),flush=True)
    if os.path.isfile(subPops):
        with open(subPops,'r') as f:
            autoSep = '\t' if '\t' in f.readlines()[0] else ','
        global subPopInfo
        subPopInfo = pd.read_table(subPops,sep=autoSep) #, sep='\t')
        if 'Sample' not in subPopInfo.columns:
            print('{colError}Error: Sample column is missing from subPops info file.{colReset}\n'.format(**globals()),flush=True)
            sys.exit()
        if len(subPopInfo.columns) < 2:
            print('{colError}Error: Unable to identify any subPop columns.{colReset}\n'.format(**globals()),flush=True)
            sys.exit()
        print('{colTime}Sub-Population File:{colReset} {}'.format(subPops, **globals()),flush=True)
        for popType in subPopInfo.columns[1:]:
            print('--{0}: {1}'.format(popType, ", ".join(sorted(set(subPopInfo[popType])))))
    print('{colTime}Min Variant Length:{colReset} {0:,}'.format(minLength, **globals()),flush=True)
    print('{colTime}Max Variant Length:{colReset} {0:,}'.format(maxLength, **globals()),flush=True)
    print('{colTime}Annotation:{colReset} {}'.format(doAnnotation, **globals()),flush=True)
    if doAnnotation:
        print('--Annotation File: {}'.format(RefFile),flush=True)
    print('{colTime}Write Variants:{colReset} {}'.format(writeVariants, **globals()),flush=True)
    print('{colTime}Write Windows:{colReset} {}'.format(writeWindows, **globals()),flush=True)
    if writeWindows:
        print('{colTime}--Window Size:{colReset} {0:,}'.format(windowSize, **globals()),flush=True)
        print('{colTime}--Window Step:{colReset} {0:,}'.format(windowStep, **globals()),flush=True)
        #print('--Window Type: {0}'.format(windowType),flush=True)
    print('{colTime}Write Samples:{colReset} {}'.format(writeSamples, **globals()),flush=True)
    print('{colTime}Write Phase:{colReset} {}'.format(PullPhasing, **globals()),flush=True)
    print('{colTime}Write Reads:{colReset} {}'.format(IncludeReads, **globals()),flush=True)
    print('{colTime}Write Adv. Quality:{colReset} {}'.format(MoreQual, **globals()),flush=True)
    if (chrSubset != ''):
        print('{colTime}Subsetting to chromosome/s:{colReset} {}'.format(', '.join(chrSubset), **globals()),flush=True)
    print('{colTime}Filtering:{colReset} {}'.format(doFiltering, **globals()),flush=True)
    if doFiltering:
        if minimumQuality != None: print('--Quality Threshold: {0}'.format(minimumQuality),flush=True)
        if minimumPrecision != None: print('--Precision Threshold: {0}'.format(minimumPrecision),flush=True)
        if maximumPercRef != None: print('--Maximum Homozygous Reference Calls Per-Variant: {0}'.format(maximumPercRef),flush=True)
        if maximumPercHet != None: print('--Maximum Heterozygous Calls Per-Variant: {0}'.format(maximumPercHet),flush=True)
        if minimumPercAlt != None: print('--Minimum Homozygous Alternative Calls Per-Variant: {0}'.format(minimumPercAlt),flush=True)
        if maximumPercMissing != None: print('--Maximum Missing Genotype Calls Per-Variant: {0}'.format(maximumPercMissing),flush=True)
        if removeIntergenic: print('--Removing Intergenic Regions.'.format(removeIntergenic),flush=True)
        if minimumPE > 0: print('--Removing variants with fewer than {0} supporting paired-end reads.'.format(minimumPE),flush=True)
        if minimumSR > 0: print('--Removing variants with fewer than {0} supporting split reads.'.format(minimumSR),flush=True)
        if minimumMAPQ > 0: print('--Removing variants with a median mapping quality below {0}.'.format(minimumMAPQ),flush=True)
    print('{colTime}Filter Gaps:{colReset} {}'.format(filterGaps, **globals()),flush=True)
    if filterGaps:
        print('{colTime}--Gaps File:{colReset} {}'.format(gapsFile, **globals()),flush=True)
    print('{colTime}Filter By Concordance:{colReset} {}'.format(filterConcordance, **globals()),flush=True)
    if filterConcordance:
        print('{colTime}--Verification Threshold:{colReset} {}'.format(percConcordance, **globals()),flush=True)
        print('{colTime}--Overlap Threshold:{colReset} {}'.format(overlapConcordance, **globals()),flush=True)
        print('{colTime}--Concordance Directory:{colReset} {}'.format(dirConcordance, **globals()),flush=True)
    print('{colTime}Calculating Fst:{colReset} {}'.format(doFst, **globals()),flush=True)
    if suppressWarnings:
        print('\nNB. Warnings are being suppressed.')

    # Do analysis, by chromosome
    if multithread and len(allChromosomes) > 1:
        printT('Beginning per-chromosome analysis, utilising {0} threads.'.format(threads))
        pool = Pool(threads)
        pool.map(analyseChr, allChromosomes)
    else:
        printT('Beginning per-chromosome analysis, without multithreading.')
        for chrChunk in allChromosomes:
            analyseChr(chrChunk)

    printT('{colDone}Analysis completed.{colReset}\n'.format(**globals()))

def prepAnnotation(RefFile, refFormat, refType, refTypeID, refCol):
    # Annotation related prep
    if doAnnotation:
        if RefFile.endswith('.gtf') or refFormat.upper() == 'GTF':
            printT('Reading in annotation reference as a .gtf file.')
            GTF = pd.read_table(RefFile,header=None,comment='#',usecols=[0,2,3,4,8],names=['Chromosome','Type','Start','End','Info'],dtype={'Chromosome':str,'Type':str,'Start':int,'End':int,'Info':str})
            GTF = GTF.loc[GTF.Type==refType]
            GTF[refCol] = GTF.Info.str.partition(refTypeID)[2].str.partition(';')[0].str.partition('"')[2].str.partition('"')[0]
            return GTF[['Chromosome','Start','End',refCol]]
        elif RefFile.endswith('.gff') or refFormat.upper() == 'GFF':
            printT('Reading in annotation reference as a .gff file.')
            GFF = pd.read_table(RefFile,header=None,comment='#',usecols=[0,2,3,4,8],names=['Chromosome','Type','Start','End','Info'],dtype={'Chromosome':str,'Type':str,'Start':int,'End':int,'Info':str})
            GFF = GFF.loc[GFF.Type==refType]
            GFF[refCol] = GFF.Info.str.partition((refTypeID+'='))[2].str.partition(';')[0]
            return GFF[['Chromosome','Start','End',refCol]]
        elif RefFile.endswith('.csv') or refFormat.upper() == 'CSV':
            printT('Reading in annotation reference as a comma-separated file.')
            return pd.read_csv(RefFile,comment='#',names=['Chromosome','Start','End','Feature'],dtype={'Chromosome':str,'Start':int,'End':int,'Feature':str},header=0,low_memory=False)
        elif RefFile.endswith('.tsv') or refFormat.upper() == 'TSV':
            printT('Reading in annotation reference as a tab-delimited file.')
            return pd.read_table(RefFile,comment='#',sep='\t',names=['Chromosome','Start','End','Feature'],dtype={'Chromosome':str,'Start':int,'End':int,'Feature':str},header=1)
        else:
            print('{colError}Error: Reference format type "'+refFormat+'" not recognised (Must be gtf, gff, csv or tsv).{colReset}\n'.format(**globals()),flush=True)
            sys.exit()

def getStats(varFile, subPops='', fileType=''):
    # Produce summary stats for a given variant or windows file.

    file = pd.read_csv(varFile, dtype={'Feature':str})

    if fileType.lower() not in ['variant','window']:
        # detect if variant or window
        fileType = 'variant' if 'Length' in file.columns else 'window'
        printT("File type auto-detected as '{0}'.".format(fileType))

    if subPops == '':
        printT('{colWarn}Nb. No population file has been provided, per-sample stats will assume all samples have variants.{colReset}'.format(**globals()))
    elif not os.path.isfile(subPops):
        printT("{colError}Error: Provided subPops '{}' does not exist.{colReset}".format(subPops, **globals()))
        sys.exit()
    else:
        numSamples = pd.read_csv(subPops).shape[0]
    print('')

    existingModels = list(set(file.Model.values)) if 'Model' in file.columns else ['SVs']

    for model in existingModels:
        subfile = file[file.Model == model] if 'Model' in file.columns else file
        numSVs = subfile.shape[0]
        if 'Model' in file.columns:
            numPerSample = list(pd.Series(pd.Series(subfile[subfile.Model==model].Samples.str.cat(sep=',').split(',')).value_counts()).values) #numPerSample = pd.Series(subfile.Samples.str.cat(sep=',').split(',')).value_counts()
        else:
            numPerSample = list(pd.Series(pd.Series(subfile.Samples.str.cat(sep=',').split(',')).value_counts()).values) #numPerSample = pd.Series(subfile.Samples.str.cat(sep=',').split(',')).value_counts()
        if subPops != '':
            numPerSample.extend([0] * (numSamples-len(numPerSample)))
        meanPerSample = np.mean(numPerSample)
        medianPerSample = np.median(numPerSample)
        minPerSample = np.min(numPerSample)
        maxPerSample = np.max(numPerSample)
        print('{0:,} {1} (mean {2:,.2f} per sample, median {3:,}, range {4:,}-{5:,})'.format(numSVs, model, meanPerSample, medianPerSample, minPerSample, maxPerSample))

        if fileType == 'variant':
            meanLen = np.mean(subfile.Length)
            medianLen = np.median(subfile.Length)
            minLen = np.min(subfile.Length)
            maxLen = np.max(subfile.Length)
            print('Sizes: (mean: {0:,.2f} bp, median: {1:,} bp, range {2:,}-{3:,} bp)'.format(meanLen, medianLen, minLen, maxLen))

            onceVar = subfile[subfile.Count == 1].shape[0]
            freqVar = subfile[subfile.Frequency >= 0.05].shape[0]
            print('Frequency: ({0:,} once ({1}%), {2:,} ({3}%) >= 5%)'.format(onceVar, round(100*onceVar/numSVs,1), freqVar, round(100*freqVar/numSVs,1)))

        if 'Feature' in subfile.columns:
            numGenic = sum(subfile.Feature.notnull())
            numInter = sum(subfile.Feature.isnull())
            print('Features: ({0:,} genic ({1}%), {2:,} ({3}%) intergenic)'.format(numGenic, round(100*numGenic/numSVs,1), numInter, round(100*numInter/numSVs,1)))

        if 'Concordance' in subfile.columns:
            zeroConcordance = subfile[subfile.Concordance == 0].shape[0]
            goodConcordance = subfile[subfile.Concordance >= percConcordance].shape[0]
            totalConcordance = subfile[subfile.Concordance == 1].shape[0]
            meanConcordance = np.mean(subfile.Concordance)
            medianConcordance = np.median(subfile.Concordance)
            print('Concordance: (none: {0:,} ({1}%), full: {2:,} ({3}%), mean: {4:,.2f}, median: {3:,.2f})'.format(zeroConcordance, round(100*zeroConcordance/numSVs,1), totalConcordance, round(100*totalConcordance/numSVs,1), meanConcordance, medianConcordance))
        print('')

if filterGaps: # Add the proper catches here later
    printT('Reading in gaps reference file as a .csv.')
    gaps = pd.read_table(gapsFile,comment='#',names=['Chromosome','Start','End'],sep=',')

# Catch, and divert to, non-standard use cases (ie. variants -> windows conversion)
if runType != 'STANDARD':
    if variantFile == '': # Currently assumes all alternative pipelines will require [a] variant file/s.
        print('{colError}Error: Please provide a variant file (or files) with --variantFile.{colReset}\n'.format(**globals()))
        sys.exit()
    if runType == 'CONVERT': # take in variant file, turn into windows file.
        if doAnnotation and os.path.exists(RefFile) != True:
            print("{colError}Error: Annotation reference file (--refFile) doesn't seem to exist.{colReset}\n".format(**globals()))
            sys.exit()
        if os.path.exists(variantFile) != True:
            print("{colError}Error: Variant file (--variantFile) doesn't seem to exist.{colReset}\n".format(**globals()))
            sys.exit()
        outDatFull = pd.read_csv(variantFile,low_memory=False)

        if chrSubset != '':
            allChromosomes = chrSubset
        elif RefFile != '':
            ref = prepAnnotation(RefFile, refFormat, refType, refTypeID, refCol)
            allChromosomes = list(ref.Chromosome.unique())    # Unlisted this appeared to sort itself in the background, listing may resolve this.
        else:
            allChromosomes = []
            for sample in samples:
                with open(sample) as f:
                    allChromosomes.append(list(set([line.split('\t')[0] for line in f.readlines if not line.startswith('#')])))
            allChromosomes = list(set(allChromosomes))
            # print('{colError}Error: Unable to infer list of chromosomes.',flush=True)
            # sys.exit()

        for chrChunk in allChromosomes:
            outDat = outDatFull.ix[outDatFull.Chromosome==chrChunk]
            if outDat.shape[0] > 0:
                doWriteWindows(outDat=outDat)
    elif runType == 'FILTER':
        doFilterVariants(variantFile)
    elif runType == 'MERGE-CHR':
        doMergeVariants(variantFile, model=MODEL)
    elif runType == 'MERGE-MODEL':
        doMergeModels(variantFile, models=MODEL, chrSubset=chrSubset)
    elif runType == 'SUBSET':
        getSubset(variantFile, region=region, feature=feature)
    elif runType == 'PREPROCESS':
        prepForVisualisation(variantFile)
    elif runType == 'STATS':
        getStats(variantFile, subPops=subPops)
    else: # Theoretically this should never be encountered, but a safety net is useful.
        print("{colError}Error: Run type '{0}' not defined.".format(runType))
        sys.exit()
else:
    # Determine chromosomes in file
    if doAnnotation:
        if os.path.isfile(RefFile):
            ref = prepAnnotation(RefFile, refFormat, refType, refTypeID, refCol)
        else:
            print('{colError}Error: Provided annotation file cannot be located.{colReset}\n'.format(**globals()))
            sys.exit()
    if chrSubset != '':
        allChromosomes = chrSubset
    elif RefFile != '':
        allChromosomes = list(ref.Chromosome.unique()) # Unlisted this appeared to sort itself in the background, listing seems to resolve this.
    else: # Without a reference annotation file, pull chromosomes from the variant files.
        allChromosomes = []
        for sample in samples:
            with open(sample) as f:
                allChromosomes.extend(list(set([line.split('\t')[0] for line in f.readlines() if not line[0] == '#'])))
        allChromosomes = list(set(allChromosomes))

    runMain()

    if mergeChr:
        import glob
        if writeVariants and len(allChromosomes) >= 2:
            printT('Merging per-chromosome variants.')
            variants = glob.glob('_'.join([outFile,MODEL,'*','variants*','v'+VERSION_NUM+'.csv']))
            if len(variants) >= 2:
                doMergeVariants(','.join(variants), model=MODEL)
            else:
                printT('Too few ({0}) per-chromosome variants to merge.'.format(len(variants)))
        if writeWindows and len(allChromosomes) >= 2:
            printT('Merging per-chromosome windows.')
            windows = glob.glob('_'.join([outFile,MODEL,'*','windows*','v'+VERSION_NUM+'.csv']))
            if len(windows) >= 2:
                doMergeVariants(','.join(windows), model=MODEL)
            else:
                printT('Too few ({0}) per-chromosome windows to merge.'.format(len(windows)))
        printT('{colTitle}Merge complete.{colReset}\n'.format(**globals()))

    # Brush log files under the carpet
    if not os.path.exists('./SVPop_Logs'):
        os.makedirs('./SVPop_Logs')
    os.system('mv *{0}*.log ./SVPop_Logs'.format(MODEL))