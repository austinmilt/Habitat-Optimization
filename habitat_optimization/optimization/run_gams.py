import sys
sys.path = ['../data_processing'] + sys.path
from make_gdx import MAK_DEF_DDN, MAK_DEF_RDN

# run()
RUN_EXT_GDX = '.gdx'
RUN_EXT_CSV = '.csv'
RUN_GMS = 'Habitat_Opt.gms'
RUN_GRF = 'data_run.gdx'
RUN_GDF = 'data_all.gdx'
RUN_GOF = 'results.gdx'


# ~~ run() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def run(indir, outfile, defGDXStr=MAK_DEF_DDN, runGDXStr=MAK_DEF_RDN):
    """
    RUN() runs a series of GAMS models, substituting the current run GDX in
    each run and outputting the results to a CSV.
    
    INPUTS:
        indir       = directory where GDXs are stored
        outfile     = output summary CSV to be created
        defGDXStr   = (optional) name (without extension) of default GDX in
            [workingDir]. Default is take from make_gdx
        runGDXStr   = (optional) name prefix (without extension) of
            run-specific GDXs. Default is taken from make_gdx.
        
    OUTPUTS:
        series of run result CSV file paths
    """
    
    # imports
    from glob import glob
    from gdx_to_csv import gdx_to_csv, concatenate_csvs
    import os, shutil, subprocess
    
    # get input gdxs and identify default gdx
    defGDXs = [os.path.abspath(f) for f in glob(os.path.join(indir, defGDXStr + '*%s' % RUN_EXT_GDX))]
    assert len(defGDXs) == 1, 'Unable to determine which GDX is the default.'
    defGDX = defGDXs[0]
    runGDXs = [os.path.abspath(f) for f in glob(os.path.join(indir, runGDXStr + '*%s' % RUN_EXT_GDX))]
    
    # set up for runs
    thisdir = os.path.abspath(os.path.dirname(__file__))
    gamsOutGDX = os.path.join(thisdir, RUN_GOF)
    tempFiles = set()
    
    try:
        
        # run GAMS and output results
        csvs = []
        for gdx in runGDXs:
            
            # run the model
            subprocess.call(
                'gams %s --defaultgdx "%s" --rungdx "%s"' % (RUN_GMS, defGDX, gdx)
            )
            
            # convert results to CSV
            outCSV = os.path.join(thisdir, os.path.basename(gdx).split('.', 1)[0] + RUN_EXT_CSV)
            gdx_to_csv(gamsOutGDX, outCSV)
            tempFiles.add(gamsOutGDX)
            tempFiles.add(outCSV)
            csvs.append(outCSV)
            
        # concatenate csvs
        concatenate_csvs(csvs, outfile)
        return outfile
            
    # delete temporary files
    finally:
        for f in tempFiles:
            try: os.remove(f)
            except: print 'Could not delete temporary file %s' % f

            
if __name__ == '__main__':
    import os
    thisdir = os.path.abspath(os.path.dirname(__file__))
    print run(
        os.path.join(thisdir,r'..\test\data\gdxs'), 
        os.path.abspath(os.path.join(thisdir,r'..\test\results'))
    )