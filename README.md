# SV-Pop
_Public documentation currently in development_

SV-Pop is designed for post-discovery SV analysis and visualisation, and therefore has two modules for those purposes. Both modules should work out of the box, but it's a good idea to run setup.py (in Analysis/) to check that all dependencies are installed, and optionally add SVPop to your PATH.

<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Pipeline.png" alt="Pipeline Overview" width="400"/>

## Analysis Module
<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Preview_Analysis.png" alt="Preview Analysis" width="800"/>

Quick start:
```bash
SVPop -h
```

- DEFAULT
- CONVERT
- FILTER
- MERGE-CHR
- MERGE-MODEL
- SUBSET
- STATS
- PREPROCESS

Input > Process > Output

## Visualisation Module
<img src="https://raw.githubusercontent.com/mattravenhall/SV-Pop/master/Images/Preview_Visualisation.png" alt="Preview Visualiser"/>

Quick start:
```bash
SVPop --PREPROCESS --variantFile=PREFIX
Rscript easyRun.r
```

- Annotation file
- Population file
- Variants output
- Windows output

## Citation
Ravenhall M XXXXXXXXXXXXXXXX.
