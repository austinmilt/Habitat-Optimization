#!/usr/bin/python

# imports
from glob import glob
import os, shutil, subprocess

# inputs/constants
GDX_LOC = '../gdxs'
RES_LOC = '../results'
RUN_LOC = '../runs'
GDX_SCH = '*.gdx'
RUN_DIR_PRE = 'run_%i'
DEF_PRE = 'data_all'
RUN_PRE = 'data_run'
GMS_FIL = 'Habitat_Opt.gms'
CND_FIL = 'condor_gams_submit' 

# short function to get run number from run gdx file name
gdx2run = lambda s: int(os.path.basename(s).split('.')[0][len(RUN_PRE):])

# loop over runs, creating and submitting a job for each one
gdxs = glob(os.path.join(GDX_LOC, GDX_SCH))
defGDX = [gdx for gdx in gdxs if os.path.basename(gdx).startswith(DEF_PRE)][0]
runGDXs = [gdx for gdx in gdxs if gdx <> defGDX]
homeDir = os.path.abspath('.')
for gdx in runGDXs:
    
    # copy run files to run directory
    run = gdx2run(gdx)
    runDir = os.path.join(RUN_LOC, RUN_DIR_PRE % run)
    if not os.path.exists(runDir): os.makedirs(runDir)
    submitFiles = [CND_FIL, defGDX, gdx, GMS_FIL]
    for f in submitFiles: shutil.copy2(f, runDir)
    
    # create the run file to be passed to condor_gams_submit
    runFile = os.path.join(runDir, 'res.run')
    baseNames = tuple([os.path.basename(f) for f in (GMS_FIL, defGDX, gdx)])
    with open(runFile, 'w') as fh:
        fh.write('hostname\n')
        fh.write("echo 'pwd'\n")
        fh.write('gams %s --defaultgdx=%s --rungdx=%s' % baseNames)
        
    # submit the job
    os.chdir(runDir)
    submitName = os.path.basename(CND_FIL)
    subprocess.call(['chmod', '777', submitName])
    callStr = ['./%s' % submitName, 'res.run' ,'%s' % ','.join(baseNames), '&']
    subprocess.call(callStr)
    os.chdir(homeDir)