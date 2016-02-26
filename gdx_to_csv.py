# Created 02/15/2016
# Updated 02/26/2016
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8
# Description:
#       This script's main purpose is to convert GAMS optimization GDX results
#   to Excel-style CSV 
#       Generally users should only need to change the options defined in the
#   very bottom section starting with if __name__ == '___main__':. Really,
#   users shouldnt need to change anything. Less frequently, the defaults
#   defined at the top of this script may be changed. Very rarely, hopefully
#   never, would interal function constants need to be changed.

# gdx_to_csv()
INP_KWD_VAL = 'value'
INP_KWD_LVL = 'level'
OUT_KWD_PAR = 'symbol'
OUT_KWD_VAL = 'value'
OUT_KWD_DIM = 'd%i'


# ~~ gdx_to_csv() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def gdx_to_csv(inGDX, outCSV):
    """
    INPUTS:
        inGDX   = absolute path to input GDX from which CSV should be made
        outCSV  = absolute path of output CSV to write
        
    OUTPUTS:
        returns outCSV, which is formatted as follows (see top of script for
        definitions of capitalized constants forming header row):
        
        OUT_KWD_PAR,OUT_KWD_DIM1,OUTKWD_DIM2,...OUT_KWD_VAL
        <symbol 1 name>,<symbol 1 1st record dimensions, comma-separated>,...<symbol 1 1st record value>,
        <symbol 2 name>,...
        ...
    """
    
    # IMPORTS
    import gams
    
    
    # LOAD DATA
    
    # set up database
    workspace = gams.GamsWorkspace()
    database = workspace.add_database_from_gdx(inGDX)
    
    # load data from database
    data = []
    maxDim = max([p.dimension for p in database])
    for parameter in database:
        for record in parameter:
            row = ['' for i in xrange(maxDim+2)]
            row[0] = parameter.name
            row[1:len(record.keys)+1] = record.keys
            
            # some records have a 'value' while others have a 'level',
            #   both of which are the value. So take either one if it
            #   has it.
            if hasattr(record, 'value'): row[-1] = str(record.value)
            elif hasattr(record, 'level'): row[-1] = str(record.level)
            data.append(row)
            
    # WRITE OUTPUT
    with open(outCSV, 'w') as fh:
    
        # write the header
        headerList = ['parameter']
        headerList.extend(['d%i' % i for i in xrange(maxDim)])
        headerList.append('value')
        fh.write(','.join(headerList))
        
        # write the rows of output data
        for row in data:
            fh.write('\n' + ','.join(row))
            
    # FINISH
    return outCSV
    
    
if __name__ == '__main__':

    import os
    
    # define default inputs
    thisDir = os.path.abspath(os.path.dirname(__file__))
    inGDX = os.path.join(thisDir, 'results.gdx')
    outCSV = os.path.join(thisDir, 'results.csv')
    gdx_to_csv(inGDX, outCSV)
    