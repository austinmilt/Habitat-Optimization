
# imports
import shutil, os
from glob import glob

# inputs/parameters
runDir = '../runs'
searchStr = 'run_*/results.gdx'
resultDir = '../results'
gdxExt = '.gdx'

# pool gdxs
gdxs = glob(os.path.join(runDir, searchStr))
if not os.path.exists(resultDir): os.makedirs(resultDir)
for gdx in gdxs:
    gdxName = os.path.basename(gdxExt).rsplit(gdxExt,1)
    run = gdx.split(os.sep)[-2]
    newName = os.path.join(resultDir, run+gdxExt)
    shutil.copy2(gdx, newName)