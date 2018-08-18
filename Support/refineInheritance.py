#SVPop Remove Non-Inherited
import sys
import pandas as pd

def addSVID(variantFile):
	x = pd.read_csv(variantFile, low_memory=False)
	return(x.assign(SVID = x.Chromosome.map(str) + ':' + x.Start.map(str) + '-' + x.End.map(str) + '_' + x.Model.map(str)))

def writeDict(dictionary, filename):
	with open(filename, 'w') as f:
		for k, v in dictionary.items():
			f.write('{0},{1}\n'.format(k, v))

def addInheritance(parentFile, childrenFile, relationships):
	# read input files
	print('Reading in parents')
	SVs_parents = addSVID(parentFile)
	SVs_children = addSVID(childrenFile)
	relationships = pd.read_csv(relationships)

	parents = relationships.Parent  # Parent,Child,etc
	children = relationships.Child

	# Holders
	inherited = set()
	inheritedAll = set()
	not_inherited = set()
	not_inheritedAll = set()
	perc_inherited = {}
	perc_not_inherited = {}

	print('Looping parents')
	for parent in parents:
		try:
			child = list(relationships.Child[relationships.Parent == parent])[0]
		except KeyError:
			print('No child for {}'.format(parent))
			continue

		print('\n[Parent] {0} : {1} [Child]'.format(parent, child))

		SVs_parent = SVs_parents[SVs_parents.Samples.str.contains(parent)]
		SVs_child = SVs_children[SVs_children.Samples.str.contains(child)]

		if SVs_parent.shape[0] == 0:
			print("No variants for parent '{}'.".format(parent))
		else:
#			print(SVs_parent.SVID[SVs_parent.SVID.isin(SVs_child.SVID)].values)


			inherited = set(SVs_parent.SVID[SVs_parent.SVID.isin(SVs_child.SVID)].values)
			inheritedAll.update(inherited)
			perc_inherited[parent] = 100 * len(inherited) / SVs_parent.shape[0]
			print("{0:.1f}% inherited for parent {1}.".format(perc_inherited[parent], parent))

			not_inherited = set(SVs_parent.SVID[~SVs_parent.SVID.isin(SVs_child.SVID)].values)
			not_inheritedAll.update(not_inherited)
			perc_not_inherited[parent] = 100 * len(not_inherited) / SVs_parent.shape[0]

	print("\nSubsetting to inherited only file, prefix: '{}'.".format(prefix))
	SVs_parents = SVs_parents.loc[SVs_parents.SVID.isin(inherited)]
	SVs_parents.to_csv('{0}_inherited.csv'.format(prefix))

	print("Writing inheritence dictionaries to file, prefix: '{}'.".format(prefix))
	writeDict(perc_inherited, '{0}_percInherited.csv'.format(prefix))
	writeDict(perc_not_inherited, '{0}_percNotInherited.csv'.format(prefix))

# Parse command line arguments
if len(sys.argv) < 3:
	print('refineInheritance.py <parent_variants> <child_variants> <relationships> (<prefix>)')
	sys.exit()
else:
	pfile = sys.argv[1]
	cfile = sys.argv[2]
	rfile = sys.argv[3]
	if len(sys.argv) > 4:
		prefix = sys.argv[4]
	else:
		prefix = 'Default'
	print('= refineInheritance.py v1.0 =')
	print('Parents: '+pfile)
	print('Children: '+cfile)
	print('Relations: '+rfile)
	addInheritance(pfile, cfile, rfile)
