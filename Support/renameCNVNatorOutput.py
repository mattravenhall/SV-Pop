#!/usr/bin/env python3
import os

vcfdir='/home/matt/Plasmodium/Pf_SV/Data'

for ID in os.listdir(vcfdir):
	nameID = '_'.join(ID.split('.')[0].split('_')[:-1])
	coreID = nameID.split('_')[-1]
	if coreID[:3] == 'ERR':
		os.system('cp {0}.cnvs {1}_DEL.cnvs'.format(coreID, nameID))
		os.system('cp {0}.cnvs {1}_DUP.cnvs'.format(coreID, nameID))
