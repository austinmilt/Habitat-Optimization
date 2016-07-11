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
OUT_KWD_FIL = 'file'

# ~~ make_header ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def make_header(ndim):
    """Short function shared between functions here to make file headers."""
    return [OUT_KWD_PAR] + [OUT_KWD_DIM % i for i in range(ndim)] + [OUT_KWD_VAL]
    

# ~~ gdx_to_csv() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def gdx_to_csv(inGDX, outCSV):
    """
    GDX_TO_CSV() converts a GDX to CSV
    
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
    import gams, csv
    
    
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
            if hasattr(record, INP_KWD_VAL): row[-1] = str(record.value)
            elif hasattr(record, INP_KWD_LVL): row[-1] = str(record.level)
            data.append(row)
            
    # WRITE OUTPUT
    writer = csv.writer(open(outCSV, 'wb'))
    header = make_header(maxDim)
    writer.writerow(header)
    for row in data: writer.writerow(row)
            
    # FINISH
    return outCSV
    
    
# ~~ concatenate_csvs() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def concatenate_csvs(csvs, outCSV):
    """
    CONCATENATE_CSVS() concatenates multiple CSVs as returned by gdx_to_csv()
    into a single file
    
    INPUTS:
        csvs    = paths to csvs to be concatenated
        outCSV  = path to output CSV to create
    
    OUTPUTS:
        outCSV, which will have the same format as returned by gdx_to_csv(),
        but with an extra column denoting the filename from which the results
        were taken.
        
    NOTES:
        o if csvs[] contains multiple files with the same file name, you will
          not be able to distinguish between them in the output
    """
    
    # imports
    import csv, os
    
    # read csvs
    names = set()
    data = []
    maxDim = 0
    for csvFile in csvs:
    
        # check for duplicate names
        csvName = os.path.splitext(os.path.basename(csvFile))[0]
        if csvName in names:
            print ''.join((
                'WARNING: Found duplicate name %s. ' % csvName,
                'You will not be able to distinguish multiple results because ',
                'of this.'
            ))
        names.add(csvName)
        
        # get data from the file
        reader = csv.reader(open(csvFile, 'r'))
        maxDim = max(maxDim, len(reader.next())-2)
        data.extend([[csvName] + row for row in reader])
        
    # write output csv
    writer = csv.writer(open(outCSV, 'wb'))
    header = [OUT_KWD_FIL] + make_header(maxDim)
    writer.writerow(header)
    for row in data:
        nExtraDim = maxDim-len(row)
        outRow = row[:-1] + ['' for i in range(nExtraDim)] + [row[-1]]
        writer.writerow(outRow)
        
    return outCSV
    
        
if __name__ == '__main__':

    import os
    
    # define default inputs
    thisDir = os.path.abspath(os.path.dirname(__file__))
    inGDX = os.path.join(thisDir, 'results.gdx')
    outCSV = os.path.join(thisDir, 'results.csv')
    gdx_to_csv(inGDX, outCSV)
    