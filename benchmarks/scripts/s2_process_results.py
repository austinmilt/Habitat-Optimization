#!/usr/bin/python

# imports
from gdx_to_csv import gdx_to_csv, concatenate_csvs
from glob import glob
import os

# inputs/parameters
resultDir = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\benchmarks\results'
searchStr = r'*run_*.gdx'
resultCSV = r'results.csv'

# create individual csvs in each directory
gdxs = glob(os.path.join(resultDir, searchStr))
csvs = []    
for gdx in gdxs:
    runName = os.path.basename(gdx).split('.')[0]+'.csv'
    outcsv = os.path.join(os.path.abspath(os.path.dirname(gdx)), runName)
    csvs.append(gdx_to_csv(gdx, outcsv))
    
# concatenate csvs
concatenate_csvs(csvs, resultCSV)

for f in csvs:
    os.remove(f)