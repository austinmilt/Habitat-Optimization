from make_gdx import MAK_DEF_DDN, MAK_DEF_RDN

# run()
RUN_EXT_GDX = '.gdx'
RUN_EXT_CSV = '.csv'
RUN_GMS = 'Habitat_Opt.gms'
RUN_GRF = 'data_run.gdx'
RUN_GDF = 'data_all.gdx'
RUN_GOF = 'results.gdx'


# ~~ run() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def run(indir, outdir, defGDXStr=MAK_DEF_DDN, runGDXStr=MAK_DEF_RDN):
    """
    RUN() runs a series of GAMS models, substituting the current run GDX in
    each run and outputting the results to a CSV.
    
    INPUTS:
        indir       = directory where GDXs are stored
        outdir      = directory where GDXs should be saved. If it doesnt exist
            it will be created
        defGDXStr   = (optional) name (without extension) of default GDX in
            [workingDir]. Default is take from make_gdx
        runGDXStr   = (optional) name prefix (without extension) of
            run-specific GDXs. Default is taken from make_gdx.
        
    OUTPUTS:
        series of run result CSV file paths
    """
    
    # imports
    from glob import glob
    from gdx_to_csv import gdx_to_csv
    import os, gams, shutil
    
    # get input gdxs and identify default gdx
    defGDXs = glob(os.path.join(indir, defGDXStr + '*%s' % RUN_EXT_GDX))
    assert len(defGDXs) == 1, 'Unable to determine which GDX is the default.'
    defGDX = defGDXs[0]
    runGDXs = glob(os.path.join(indir, runGDXStr + '*%s' % RUN_EXT_GDX))
    
    # set up for runs by creating GAMS workspace, making directories, etc
    thisdir = os.path.abspath(os.path.dirname(__file__))
    workspace = gams.GamsWorkspace(thisdir)
    job = workspace.add_job_from_file(RUN_GMS)
    gamsDefGDX = os.path.join(thisdir, RUN_GDF)
    gamsRunGDX = os.path.join(thisdir, RUN_GRF)
    gamsOutGDX = os.path.join(workspace.working_directory, RUN_GOF)
    if not os.path.exists(outdir): os.makedirs(outdir)
    shutil.copy2(defGDX, gamsDefGDX)
    tempFiles = set([gamsDefGDX])
    
    try:
        
        # run GAMS and output results
        outfiles = []
        for gdx in runGDXs:
            
            # copy run files to correct location
            shutil.copy2(gdx, gamsRunGDX)
            tempFiles.add(gamsRunGDX)
            
            # run the model
            job.run(create_out_db=False)
            
            # convert results to CSV
            outCSV = os.path.join(outdir, os.path.basename(gdx).split('.', 1)[0] + RUN_EXT_CSV)
            gdx_to_csv(gamsOutGDX, outCSV)
            tempFiles.add(gamsOutGDX)
            outfiles.append(outCSV)
            
        return outfiles
            
    # delete temporary files
    finally:
        for f in tempFiles:
            try: os.remove(f)
            except: print 'Could not delete temporary file %s' % f

            
if __name__ == '__main__':
    import os
    thisdir = os.path.abspath(os.path.dirname(__file__))
    print run(os.path.join(thisdir,'test_data'), os.path.join(thisdir,'test_results'))