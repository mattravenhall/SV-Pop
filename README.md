# SV-Pop
_Public documentation currently in development_

SV-Pop is designed for post-discovery SV analysis and visualisation, and therefore has two modules for those purposes. Both modules should work out of the box, but it's a good idea to run setup.py (in Analysis/) to check that all dependencies are installed, and optionally add SVPop to your PATH.

<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Pipeline.png" alt="Pipeline Overview" width="400"/>

## Analysis Module
<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Preview_Analysis.png" alt="Preview Analysis" width="800"/>

### Quick start:
```bash
SVPop -h
```

### Functions
- `DEFAULT`: Process individual vcf files to population-level lists.
- `CONVERT`: Convert a variant output file into a window file.
- `FILTER`: Filter a variant output file by a range of factors.
- `MERGE-CHR`: Merge per-chromosome variants files into one file.
- `MERGE-MODEL`: Merge by-model variants files into one file.
- `SUBSET`: Create a subset of a given variant or window file.
- `STATS`: Produce summary statistics for a variant or window files.
- `PREPROCESS`:	Process analysis output files for visualisation.

## Visualisation Module
<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Preview_Visualisation.png" alt="Preview Visualiser"/>

### Quick start:
```bash
SVPop --PREPROCESS --variantFile=PREFIX
Rscript easyRun.r
```
### Input Files
- `Annotation file`: 
- `Population file`: 
- `Variants output`: 
- `Windows output`: 

## Citation
Ravenhall M XXXXXXXXXXXXXXXX.
