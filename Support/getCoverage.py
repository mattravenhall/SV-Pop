#!/usr/bin/env python3

#########################
# getCoverage.py        #
# Simple coverage plots #
# Matt Ravenhall        #
#########################

# Import all the things please
import os
import sys
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

plt.rc('font', size=7)
plt.rc('xtick', labelsize=5)

covStore = './'
outDirectory = './'
threads = 5
title = ''
plots = []
filename='testCoverage'
neighbours=''
genes='None'
SVs=''    # This should be an SV-Pop output file.

if len(sys.argv) == 1 or sys.argv[1].lower() == 'help':
	print('\n\033[92mCoverage Plotter\033[0m\n'+
	'\033[94mRequired:\n'+
	'\t--region=chromosome:basepair-basepair\n'+
	'\t--samples=ID,ID,ID,ID\n'+
	'Optional:\n'+
	'\t--genes=basepair-basepair,basepair-basepair\n'+
	'\t--SVs=/path/to/variants\n'+
	'\t--SVModel=SV model type\n'+
	'\t--threads=int\n'+
	'\t--covStore=/path/to/dir\n'+
	'\t--title=string\n'+
	'\t--plots=string,string,string\n'+
	'\t--filename=string\n'+
	'\t--neighbours=/path/to/annotation\033[0m\n')
	sys.exit()

def checkArg(valueGiven, givenArg, isBool=False):
    try:
        outValue = valueGiven.split('=')[1]
    except IndexError:
        print('\033[91mError: No argument supplied to '+givenArg+'.\033[0m\n',flush=True)
        sys.exit()
    if outValue == '':
        print('\033[91mError: No argument supplied to '+givenArg+'.\033[0m\n',flush=True)
        sys.exit()
    if isBool and (outValue.lower() in ['t','true']):
        return(True)
    elif isBool and (outValue.lower() in ['f','false']):
        return(False)
    elif isBool:
        print('\033[91mError: Incorrect argument "'+outValue+'" supplied to '+givenArg+'.\033[0m\n',flush=True)
        sys.exit()
    else:
        return(outValue)

for arg in sys.argv[1:]:
	if arg.startswith('--region'):
		chromosome, region = checkArg(arg, '--region').split(':')
		regionStart, regionEnd = region.split('-')
	elif arg.startswith('--samples'):
		samples = checkArg(arg, '--samples').split(',')
	elif arg.startswith('--genes'):
		genes = checkArg(arg, '--genes').split(',')
	elif arg.startswith('--neighbours'):
		neighbours = checkArg(arg, '--neighbours')
		if os.path.isfile(neighbours):
			neighbours = pd.read_table(neighbours)
		else:
			print("Neighbours file doesn't exist.")
			sys.exit()
	elif arg.startswith('--SVs'):
		SVs = checkArg(arg, '--SVs')
		if os.path.isfile(SVs):
			SVs = pd.read_csv(SVs)
		else:
			print("SV file doesn't exist.")
			sys.exit()
	elif arg.startswith('--SVModel'):
		SVModel = checkArg(arg, '--SVModel')
	elif arg.startswith('--threads'):
		threads = int(checkArg(arg, '--threads'))
	elif arg.startswith('--covStore'):
		covStore = checkArg(arg, '--covStore')
		if not os.path.isdir(covStore):
			print('Given covStore directory does not exist')
			sys.exit()
	elif arg.startswith('--outDir'):
		outDirectory = checkArg(arg, '--outDir')
		if not os.path.isdir(outDirectory):
			print('Given outDir directory does not exist')
			sys.exit()
	elif arg.startswith('--title'):
		title = checkArg(arg, '--title')
	elif arg.startswith('--filename'):
		filename = checkArg(arg, '--filename')
	elif arg.startswith('--plots'):
		plots = checkArg(arg, '--plots').split(',')
	else:
		print('\033[91mArgument {0} not recognised.\033[0m\n'.format(arg))
		sys.exit()

missingVar = []
for var in ['region', 'samples', 'genes', 'SVs']:
	if var not in locals():
		missingVar.append(var)
if len(missingVar) > 0:
	print('Missing required variables: {0}'.format(missingVar))
	sys.exit()
if len(plots) != 0 and len(plots) != len(samples):
	print('Incorrect number of plot y labels: {0} labels for {1} samples.'.format(len(plots), len(samples)))
	sys.exit()

if 'Model' in SVs.columns:
	SVs = SVs[(SVs.Chromosome == chromosome) &(SVs.Start < int(regionEnd)) & (SVs.End > int(regionStart)) & (SVs.Model == SVModel)] if SVs is not '' else ''
else:
	SVs = SVs[(SVs.Chromosome == chromosome) &(SVs.Start < int(regionEnd)) & (SVs.End > int(regionStart))] if SVs is not '' else ''
neighbours = neighbours[(neighbours.Chromosome == chromosome) & (neighbours.Start < int(regionEnd)) & (neighbours.End > int(regionStart))] if neighbours is not '' else ''

print('Running Coverage Pipeline For:')
print(' Region: {0} ({1:,} bp)'.format(region,int(regionEnd)-int(regionStart)))
print(' Sample/s: {0}'.format(samples))
print(' Gene/s: {0}'.format(genes))
#print(' SV/s: {0}'.format(SVs))
#print(' Neighbouring Genes: {0}'.format(neighbours))
print(' Threads: {0}'.format(threads))
print(' Path To Coverage: {0}'.format(covStore))
print(' Figure Title: {0}'.format(chromosome+':'+region if title == '' else title))
print(' Output Filename: {0}.png'.format(filename))
print('')

#################################################################################
# Grab Coverage #
#################

print('Grabbing Coverage Subsets')
commands = ["awk -F $'\t' '{ if ($1 == \""+chromosome+"\" && $2 > "+regionStart+" && $2 < "+regionEnd+") print $0 }' <(zcat -dc "+covStore+sample+".coverage.gz) | gzip > "+sample+'_'+chromosome+':'+region+".cov.gz" for sample in samples]
processes = [subprocess.Popen(['/bin/bash','-c',cmd]) for cmd in commands]
print(' Waiting for {0} subprocess(es).'.format(len(processes)))
for p in processes: p.wait()
print('')

#################################################################################
# Plot Coverage #
#################

print('Creating Coverage Plot')
fig, ax = plt.subplots(nrows=len(samples), ncols=1,figsize=(8,1.2*len(samples)))

if len(samples) == 1:
	sample = samples[0]
	covFile = pd.read_csv('{0}_{1}:{2}-{3}.cov.gz'.format(sample,chromosome,regionStart,regionEnd), compression='gzip', header=None, sep='\t')

	ax.plot(covFile[1], covFile[2], lw=0.5)
	ax.set_title(chromosome+':'+region if title == '' else title)
	ax.set_xlim(int(regionStart), int(regionEnd))
	ax.set_xlabel('Position (bp)')
	if len(plots) == 0:
		ax.set_ylabel(sample)
	else:
		ax.set_ylabel(plots[0])

	if SVs is not '':
		SVs = SVs[(SVs.Samples.str.contains(sample))]
		for _, s in SVs.iterrows():
			start = s['Start']
			end = s['End']
			ax.axvspan(start, end, facecolor='orange', alpha=0.3, edgecolor='none')
	if genes is not 'None':
		for g in genes:
			start, end = g.split('-')
			ax.axvspan(start, end, facecolor='green', alpha=0.2, edgecolor='none')
	if neighbours is not '':
		for _, n in neighbours.iterrows():
			start = n['Start']
			end = n['End']
			ax.axvspan(start, end, facecolor='grey', alpha=0.2, edgecolor='none')
	ax.axhline(y=0,color='black',lw=0.5)
	
	covStats = '{0}{1}.bam.stats'.format(covStore,sample)
	if os.path.isfile(covStats):
		with open(covStats) as f:
			meanCov = [float(l.rstrip('\n').split(' ')[1]) for l in f.readlines() if 'Mean:' in l][0]
		ax.axhline(y=meanCov,color='red',lw=0.5,linestyle='dashed')

else:
	for i, sample in enumerate(samples):
		covFile = pd.read_csv('{0}_{1}:{2}-{3}.cov.gz'.format(sample,chromosome,regionStart,regionEnd), compression='gzip', header=None, sep='\t')

		ax[i].plot(covFile[1], covFile[2], lw=0.5)
		if i == 0: ax[i].set_title(chromosome+':'+region if title == '' else title)
		ax[i].set_xlim(int(regionStart), int(regionEnd))
		ax[i].set_xlabel('Position (bp)')
		if len(plots) == 0:
			ax[i].set_ylabel(sample)
		else:
			ax[i].set_ylabel(plots[i])
		
		if SVs is not '':
			SVs_sub = SVs[(SVs.Samples.str.contains(sample))]
			for _, s in SVs_sub.iterrows():
				start = s['Start']
				end = s['End']
				ax[i].axvspan(start, end, facecolor='orange', alpha=0.3, edgecolor='none')
		if genes is not 'None':
			for g in genes:
				start, end = g.split('-')
				ax[i].axvspan(start, end, facecolor='green', alpha=0.2, edgecolor='none')
		if neighbours is not '':
			for _, n in neighbours.iterrows():
				start = n['Start']
				end = n['End']
				ax[i].axvspan(start, end, facecolor='grey', alpha=0.2, edgecolor='none')
		ax[i].axhline(y=0,color='black',lw=0.5)

		covStats = '{0}{1}.bam.stats'.format(covStore,sample)
		if os.path.isfile(covStats):
			with open(covStats) as f:
				meanCov = [float(l.rstrip('\n').split(' ')[1]) for l in f.readlines() if 'Mean:' in l][0]
			ax.axhline(y=meanCov,color='red',lw=0.5,linestyle='dashed')

fig.savefig(filename+'.png', bbox_inches='tight', dpi=300)
plt.close(fig)

print('')
print('Done!')
