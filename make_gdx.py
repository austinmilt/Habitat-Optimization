# Created 02/15/2016
# Updated 03/17/2016
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8
# Description:
#       This script's main purpose is to convert barrier optimization data from
#   one format into a (or series of) GDX(s) that is used by the habitat
#   optimization GAMS model. It is designed to be as general as possible in
#   terms of the naming conventions in both the gms model and input data.
#       This script also includes a somewhat dataset-specific function, 
#   prune_barriers(), which removes rows of the input barrier data that will
#   not be relevant for any optimization. At the time of writing this
#   description (02/15/2016), the only criterion on which this pruning is based 
#   is whether a barrier is part of the network of barriers to which candidate
#   barriers  belong.
#       Generally users should only need to change the options defined in the
#   very bottom section starting with if __name__ == '___main__':. Really,
#   users shouldnt need to change anything. Less frequently, the defaults
#   defined at the top of this script may be changed. Very rarely, hopefully
#   never, would interal function constants need to be changed.

# parameters that need special exceptions in processing
EXC_BAR_NAM = 'Barriers' # on which rows in table are based

# read_gms()
GMS_KWD_SET = 'set'
GMS_KWD_ALS = 'alias'
GMS_KWD_PAR = 'parameter'
GMS_KWD_SCA = 'scalar'
GMS_KWD_OPN = '('
GMS_KWD_CLS = ')'
GMS_KWD_SEP = ','
GMS_KWD_END = ';'
GMS_KWD_WLD = '*'
GMS_KWD_LOD = '$load'
GMS_KWD_STR = "'"
GMS_TYP = {GMS_KWD_SET: str, GMS_KWD_PAR: float, GMS_KWD_SCA: float}

# load_data()
LOD_KWD_RUN = 'Run'
LOD_KWD_PAR = 'Symbol'
LOD_KWD_VAL = 'Values'
LOD_KWD_VIC = 'Values is Column Name'
LOD_KWD_SEP = ','
LOD_KWD_OPN = '('
LOD_KWD_CLS = ')'
LOD_KWD_SRC = {
    'y': True, 'yes': True, 'n': False, 'no': False, 't': True, 'f': False, 
    'true': True, 'false': False, '1': True, '0': False
}
LOD_KWD_RDF = ''
LOD_DEF_RUN = 1 


# prune_barriers()
PRN_DEF_CAN = None
PRN_DEF_RUT = '-1'
PRN_TRU = {
        '0': False, '1': True, 'true': True, 'false': False, 'no': False, 
        'yes': True, 'n': False, 'y': True
}

# make_gdx()
MAK_ZIP = '.zip'
MAK_GDX = '.gdx'
MAK_DEF_DDN = 'data_all'
MAK_DEF_RDN = 'data_run'
MAK_DEF_ZIP = False
MAK_DEF_SKP = False
MAK_KWD_RDF = 'None'


    
# ~~ PARAMETER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Parameter:

    import numpy
    
    def __init__(self, name, indices=[], description='', loadname=''):
        self.name = name
        self.indices = indices
        self.ndim = len(indices)
        self.external = False
        self.loadname = loadname
        self.description = description
        self.dtype = GMS_TYP[self.__class__.__name__.lower()]
        self.data = {}
        
        
    def __setattr__(self, attr, value):
    
        # type validation
        if attr == 'name': assert isinstance(value, (str, unicode)), 'Invalide type'
        elif attr == 'ndim': assert isinstance(value, (int, long)), 'Invalide type'
        elif attr == 'indices': assert isinstance(value, (list, tuple, set)), 'Invalide type'
        elif attr == 'external': assert isinstance(value, (bool, int)), 'Invalide type'
        elif attr == 'loadname': assert isinstance(value, (str, unicode)), 'Invalide type'
        elif attr == 'description': assert isinstance(value, (str, unicode)), 'Invalide type'
        
        # update value
        self.__dict__[attr] = value
        
        # auto-update of ndim
        if attr == 'indices': self.ndim = len(self.indices)
        
    def __repr__(self):
        return '%s <%s>' % (self.__class__.__name__, self.name)


# ~~ SET ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #        
class Set(Parameter):
    def __init__(*inputs):
        Parameter.__init__(*inputs)

# ~~ SCALAR ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Scalar(Parameter):
    def __init__(*inputs):
        Parameter.__init__(*inputs)

        
# ~~ read_gms() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def read_gms(gmsFile):
    """
    READ_GMS() loads parameters from a GAMS model file to specify necessary
    inputs from user specified data.
    
    INPUTS:
        gmsFile     = path to the GAMS model file
        
    OUTPUTS:
        dictionary of parameters/sets/aliases/scalars
    """
    with open(gmsFile, 'r') as fh:
    
        parameters = {}
        externalParameters = set()
        for line in fh:
            stripLine = line.strip()
            
            # find sets (assumes one set per line after keyword)
            if stripLine.startswith(GMS_KWD_SET):
                while True:
                    
                    # process the current set
                    newLine = fh.next().strip()
                    if newLine == '': continue
                    setName, remainder = newLine.split(GMS_KWD_OPN, 1)
                    setIndices = [s.strip() for s in remainder.split(GMS_KWD_CLS)[0].split(GMS_KWD_SEP)]
                    parameters[setName] = Set(setName, setIndices)
                    
                    # check if this is the last line of sets
                    if newLine.endswith(GMS_KWD_END): break
                    
            # find aliases
            elif stripLine.startswith(GMS_KWD_ALS):
                while True:
                    
                    # process current alias
                    newLine = fh.next().strip()
                    if newLine == '': continue
                    nameStr = newLine.split(GMS_KWD_OPN, 1)[1].rsplit(GMS_KWD_CLS, 1)[0]
                    names = [s.strip() for s in nameStr.split(GMS_KWD_SEP)]
                    for alias in names[1:]:
                        parameters[alias] = parameters[names[0]]
                    
                    # check if this is the last line of sets
                    if newLine.endswith(GMS_KWD_END): break
                    
            # find parameters
            elif stripLine.startswith(GMS_KWD_PAR):
                while True:
                
                    # process the current parameter
                    newLine = fh.next().strip()
                    if newLine == '': continue
                    paramStr, remainder = newLine.split(' ', 1)
                    if GMS_KWD_OPN not in paramStr: # zero dimension parameters
                        parameters[paramStr] = Parameter(paramStr, [])
                        
                    else: # other parameters
                        paramName, remainder = paramStr.split(GMS_KWD_OPN, 1)
                        paramIndices = [s.strip() for s in remainder.split(GMS_KWD_CLS)[0].split(GMS_KWD_SEP)]
                        parameters[paramName] = Parameter(paramName, paramIndices)
                    
                    # check if this is the last line of parameters
                    if newLine.endswith(GMS_KWD_END): break
                    
            # find scalars
            elif stripLine.startswith(GMS_KWD_SCA):
                while True:
                
                    # process the current scalar
                    newLine = fh.next().strip()
                    if newLine == '': continue
                    scalarName = newLine.split()[0]
                    parameters[scalarName] = Scalar(scalarName)
                    
                    # check if this is the last line of scalars
                    if newLine.endswith(GMS_KWD_END): break
                    
                    
            # find which parameters are to be loaded from gdx (assumes that
            #   $load statement comes only after $GDXIN)
            elif stripLine.startswith(GMS_KWD_LOD):
                _, remainder = stripLine.split(' ', 1)
                externalParameters.update([s.strip() for s in remainder.split(GMS_KWD_SEP)])
                
    # define externality of parameters
    for parameter in parameters:
        if parameter in externalParameters:
            parameters[parameter].external = True
            parameters[parameter].loadname = parameter
        
    return parameters
    
    
    
# ~~ prune_barriers() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def prune_barriers(
    tableFile, outputFile, bidColumn, downstreamColumn, **options
):
    """
    PRUNE_BARRIERS() does pre-processing of barrier data to remove any barriers
    that would not be involved in the optimization
    
    INPUTS:
        tableFile       = path to the (CSV) table dataset file, where rows are
            individual barriers and columns are barrier data/attributes
            
        outputFile      = path where the output file should be saved
        
        bidColumn      = name of the column in [tableFile] that records a
            barrier's unique ID
        
        downstreamColumn= name of the column in [tableFile] that records the
            downstream barrier ID of a barrier
            
        ** options  = (optional) keyword arguments, including:
        
            candidate_columns: list of columns in [tableFile] that denote
                which barriers rows are candidates for different projects.
                Specify None to indicate all barriers are candidates. If this
                is done, no pruning will occur based on barriers being
                in the same network as candidates. Default is PRN_DEF_CAN (
                see top of script containing this function)
                
            root_value: downstream ID value in [downstreamColumn] to indicate
                a barrier is a root (i.e. has no downstream barriers). Default
                is PRN_DEF_RUT
        
    OUTPUTS:
        path to [outputFile]
    """
    
    # imports
    import csv
    
    # update options
    P = {'candidate_columns': PRN_DEF_CAN, 'root_value': PRN_DEF_RUT}
    for k in options:
        if k.lower() in P: P[k.lower()] = options[k]
    if not isinstance(P['candidate_columns'], (list, tuple, set)):
        P['candidate_columns'] = [P['candidate_columns']]
        
    # short function to test a barrier is a candidate
    candidate = lambda x: any([PRN_TRU[v.lower()] for v in x])
    
    # load data
    reader = csv.reader(open(tableFile, 'r'))
    columns = reader.next()
    c2I = dict((columns[i], i) for i in xrange(len(columns)))
    data = dict((row[c2I[bidColumn]], row) for row in reader)
    
    # take care of the easy case (no candidate columns given)
    if P['candidate_columns'][0] is None:
        writer = csv.writer(open(outputFile, 'w'))
        writer.writerow(columns)
        for row in data.values(): writer.writerow(row)
        print 'Pruned 0 rows'
        return outputFile
        
    # go through each barrier and determine if it belongs to the network
    #   of candidate barriers by tracing downstream
    networkBarriers = set()
    for bid in data:
        
        # case 1: this barrier has already been added to the network
        #   of candidates
        if bid in networkBarriers: continue
        
        # case 2: this barrier or one of its downstream barriers is a candidate
        current = bid
        breakFlag = False
        while current <> P['root_value']:
            if candidate([data[current][c2I[k]] for k in P['candidate_columns']]):
                breakFlag = True
                
                # trace downstream, adding all downstream barriers to the
                #   network until we reach the first that has already been
                #   added (all subsequent barriers will have already been
                #   added)
                current = bid
                while current <> P['root_value']:
                    if current in networkBarriers: break
                    networkBarriers.add(current)
                    current = data[current][c2I[downstreamColumn]]
            
            # update for the next round of searching for a candidate
            if breakFlag: break
            else: current = data[current][c2I[downstreamColumn]]

    print 'Pruned %i rows' % (len(data.keys()) - len(networkBarriers))
                
    # write the output file
    writer = csv.writer(open(outputFile, 'w'))
    writer.writerow(columns)
    for bid in networkBarriers:
        writer.writerow(data[bid])
        
    return outputFile


    
# ~~ load_data() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def load_data(tableFile, settingsFile, parameters):    
    """
    LOAD_DATA() loads input data and formats it for creation of a gdx.
    
    INPUTS:
        tableFile       = Excel CSV spreadsheet where each row is a barrier and 
            columns are barrier attribute data
            
        settingsFile    = Excel CSV file with parameters not indexed by barrier 
            and column designations in tableFile. Required columns are 
                LOD_KWD_RUN (see top of Python script): run integer number. If
                    no number is given, the parameter is assumed a default
                    value to be used when missing from subsequent runs.
                LOD_KWD_PAR: parameter name and defined indices (see Notes)
                LOD_KWD_VAL: defined values or column designation for this
                    dimension of the parameter (see Notes)
                    
        parameters      = parameter dictionary as returned by read_gms()
                    
    OUTPUTS:
        dictionary of parameters with data, formatted for make_gdx()
        
    NOTES:
        o An example of a row in the settingsFile that indicates a set defined
          in the settingsFile
          
            "1","TargetsBeneficiary(Targets)","Fish1,Fish2,Fish3"
            
          where elements are separated by commas, elements are surrounded by
          double quotes, the first element is the run number, the second
          element is the parameter name with parentheses around the 
          index (or comma-separated list of indices) defined in the third
          element which is the comma-separated (or single-value) list of
          values for the Targets dimension of TargestBeneficiary
            
        o An example of a row in the settingsFile that defines a Parameter
          defined in tableFile
          
            "1","passChange(Barriers,removal,Fish1)","DELTAPASS1"
            
          where generally syntax matches above, but the third element now
          indicates the column in tableFile from which the passChange
          parameter for removal and Fish1, indexed by Barriers should
          be taken.
          
        o In the input settingsFile, the order of indices defined for a
          parameter must match the ordering in the GAMS model. Currently
          this function does not rigorously check for compatibility
    """
    
    # imports
    import csv
    
    # barrier aliases for tracking which data come from data table
    barrierAliases = set([k for k in parameters if parameters[k] is parameters[EXC_BAR_NAM]])
    
    # string conversions to different information for parameters
    def str2run(string):
        s = string.strip()
        if s == LOD_KWD_RDF: return MAK_KWD_RDF
        else: return int(s)
        
    def str2values(string):
        values = string.strip().split(LOD_KWD_SEP)
        if len(values) == 1: return values[0]
        else: return values
        
    def str2param(string):
        if LOD_KWD_OPN not in string: return (string.strip(), [None])
        paramName, remainder = string.strip().split(LOD_KWD_OPN, 1)
        indices = [s.strip() for s in remainder.rsplit(LOD_KWD_CLS, 1)[0].split(LOD_KWD_SEP)]
        return (paramName, indices)
        
    # test for whether a symbol is table.csv or definitions.csv sourced
    def is_table_sourced(string):
        return LOD_KWD_SRC.get(string.lower(), None)
    
    # read in data from definitions file
    reader = csv.reader(open(settingsFile, 'r'))
    columns = reader.next()
    c2I = dict((columns[i], i) for i in xrange(len(columns)))
    data = []
    inTable = set() # keep track of which data need to be pulled from table
    i = 0
    r = 1
    duplicateCheck = set()
    data2Param = {} # keep track of which indices in data[] belong to which parameter
    srcErrStr = ''.join([
        'User specified that the %s column for %s is not a ',
        'column name in the table CSV but %s appears as an index.'
    ])
    for row in reader:
        
        # get information on this parameter
        r += 1
        try: run = str2run(row[c2I[LOD_KWD_RUN]])
        except ValueError:
            msg = ''.join([
                'Invalid value on row %i in definitions file. Be sure to ' % r,
                'delete blank rows.'
            ])
            raise ValueError(msg)
        parameter, indices = str2param(row[c2I[LOD_KWD_PAR]])
        values = str2values(row[c2I[LOD_KWD_VAL]])
        
        # check if this is a duplicate of another row (same parameter/run)
        #   combo defined twice
        duplicateTup = (run, parameter, str(indices))
        if duplicateTup in duplicateCheck:
            msg = ''.join([
                'Repeat combinations of run + symbol + indices not allowed. ',
                'Check row %i.' % r
            ])
            raise ValueError(msg)
        else: duplicateCheck.add(duplicateTup)
        
        # add info to intermediate dict created before the final output
        #   dictionary of loaded data
        if parameter not in data2Param: data2Param[parameter] = []
        data2Param[parameter].append(i)
        data.append([run, parameter, indices, values, []])
        if len(barrierAliases.intersection(indices)) > 0:
            if not is_table_sourced(row[c2I[LOD_KWD_VIC]]):
                err = srcErrStr % (LOD_KWD_VAL, row[c2I[LOD_KWD_PAR]], EXC_BAR_NAM)
                raise AssertionError(err)
            inTable.add(i)
        elif len(barrierAliases.intersection([parameter])) > 0:
            if not is_table_sourced(row[c2I[LOD_KWD_VIC]]):
                err = srcErrStr % (LOD_KWD_VAL, row[c2I[LOD_KWD_PAR]], EXC_BAR_NAM)
                raise AssertionError(err)
            inTable.add(i)
        i += 1
        
    # read in data from table file based on definitions
    reader = csv.reader(open(tableFile, 'r'))
    columns = reader.next()
    c2I = dict((columns[i], i) for i in xrange(len(columns)))
    for row in reader:
        for i in inTable:
            entryColumn = data[i][3]
            value = row[c2I[entryColumn]]
            data[i][4].append(value)

    # add data to parameter objects, converting to the proper data format
    #   as we go
    outParams = {}
    for paramKey in parameters:
        if not parameters[paramKey].external: continue
        
        # find a parameter key from parameters dict that matches something
        #   in the data files
        aliases = [k for k in parameters if parameters[k] is parameters[paramKey]]
        paramNames = [row[1] for row in data if row[1] in aliases]
        if len(paramNames) > 0: paramName = paramNames[0]
        else: continue
        
        # process one dimension of the data for the current parameter
        dataIndices = data2Param[paramName]
        pParent = parameters[paramName]
        outParams[paramName] = {}
        for i in dataIndices:
            run, _, subIndices, valOrCol, noneOrVal = data[i]
            
            # create new parameter to store data in based on parameter
            #   from read_gms()
            if run not in outParams[paramName]:
                outParams[paramName][run] = pParent.__class__(
                    pParent.name, pParent.indices, pParent.description, 
                    pParent.loadname
                )
            parameter = outParams[paramName][run]
            
            # convert values to correct format
            if len(noneOrVal) == 0: values = valOrCol
            else: values = noneOrVal
            if isinstance(values, (list, tuple)):
                values = [parameter.dtype(s) for s in values]
            else: values = parameter.dtype(values)
                
            # add data to parameter data dictionary
            subdict = parameter.data
            for j in xrange(parameter.ndim-1):
                index = subIndices[j]
                if index not in subdict: subdict[index] = {}
                subdict = subdict[index]
            if subIndices[-1] is None: parameter.data = values
            else: subdict[subIndices[-1]] = values
            
        # update all aliases as well
        for k in aliases: outParams[k] = outParams[paramName]

    return outParams
    
    
    
# ~~ make_gdx() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def make_gdx(
    data, outputDirectory, defGDXName=MAK_DEF_DDN, runGDXPref=MAK_DEF_RDN,
    parameters=None, zip=MAK_DEF_ZIP, skip=MAK_DEF_SKP
):
    """
    MAKE_GDX() uses data loaded by load_data() to make gdx gams databases
    for individual model runs, where there is one gdx shared across all runs
    and a series of gdx's, one for each run
    
    INPUTS:
        data                = data dictionary as returned by load_data()
        outputDirectory     = directory where gdx's should be saved
        defGDXName          = (optional) name of the GDX to be created that 
            contains data not changing across runs. Default is MAK_DEF_DDN
            (see top of script for constants)
        runGDXPref          = (optional) name prefixfor run-specific gdx file
            names, without the extension. The run number is appended to each file
            name. Default is MAK_DEF_RDN.
        parameters          = (optional) GMS model parameters as returned by
            read_gms(). If supplied, this function will attempt to fill inany
            missing, necessary data definitions not in data{} with empty
            data expected by GAMS. Default is None, which will result in this
            being skipped and probable failure of GAMS execution when data
            are missing.
        zip                 = (optional) if True, each output GDX is zipped
            to reduce file size. Default is MAK_DEF_ZIP.
        skip                = (optional) if True, skips runs for which a file
            already exists that matches the output file name (could be .zip or
            .gdx). Default is MAK_DEF_SKP
    
    OUTPUTS:
        list of paths to the saved gdx files
    """
    
    import os, zipfile, gams
    
    # dictionary traversion for traversing over parameter definitions
    #   dictionary and getting all values
    class Node(object):
        def __init__(self, nodeData, key=None, parent=None):
            self.parent = parent
            self.children = []
            self.key = key
            if isinstance(nodeData, dict):
                for k in nodeData:
                    self.children.append(Node(nodeData[k], k, self))
            else:
                self.children.append(nodeData)
                
        def trace_up(self):
            keys = []
            cur = self
            while cur.parent is not None:
                keys.append(cur.key)
                cur = cur.parent
            return keys[::-1]
        
        def traverse(self):
            stack = [self]
            while len(stack) > 0:
                cur = stack.pop()
                for child in cur.children:
                    if isinstance(child, Node):
                        stack.append(child)
                    else:
                        yield (cur.trace_up(), child)
                        
    # get list of indices for run identities
    runIndices = set()
    for k in data:
        runIndices.update(data[k].keys())
    try:
        runIndices.remove(MAK_KWD_RDF)
        defRun = MAK_KWD_RDF
    except KeyError:
        defRun = min(runIndices)
        print ''.join((
            'Could not find the default run index %s. ' % str(MAK_KWD_RDF),
            'Assuming default values should be taken from run %i.' % defRun
        ))
    runIndices = [-1] + sorted(runIndices) # append one for the default gdx
    
    # get list of parameters that dont change across runs so we know which to
    #   put in default vs run-specific gdxs
    #   NOTE: Because GAMS gives zero-dimensional parameters (scalars) a value
    #   of zero (rather than empty), do not include those in this list.
    parDefOnly = set()
    for k in data:
        if (len(data[k]) == 1) and (data[k][data[k].keys()[0]].ndim <> 0):
            parDefOnly.add(k)

            
    # ~~ MAKE GDXS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    outfiles = []
    for run in runIndices:
    
        # check if this run gdx already exists, and skip if it does
        if skip:
            if run == -1: outname = os.path.join(outputDirectory, defGDXName)
            else: outname = os.path.join(outputDirectory, '%s%i' % (runGDXPref, run))
            if zip: outfile = outname + MAK_ZIP
            else: outfile = outname + MAK_GDX
            if os.path.exists(outfile):
                print ''.join((
                    'WARNING: Found GDX for Run %i. Skipping creation. ' % run,
                    'To avoid this, set skip=False'
                ))
                continue
        
        # add parameters to the database
        workspace = gams.GamsWorkspace()
        database = workspace.add_database()
        dbVars = {}
        for pName in data:
        
            # initialize the parameter in the database
            if run == -1: parameter = data[pName][defRun]
            else:
                try: parameter = data[pName][run]
                except KeyError: parameter = data[pName][defRun]
            if pName <> parameter.loadname: continue # avoid duplicate entries for aliases
            if isinstance(parameter, Set): 
                dbVars[pName] = database.add_set(parameter.name, parameter.ndim)
            elif isinstance(parameter, (Parameter, Scalar)): 
                dbVars[pName] = database.add_parameter(parameter.name, parameter.ndim)
                
            # for the default gdx, skip parameters that will be in the run-specific gdxs
            #   and vice-versa for run-specific gdxs
            if (run == -1) and (pName not in parDefOnly): continue
            elif (run <> -1) and (pName in parDefOnly): continue
            
            # loop over parameter data, adding records to the database as we go
            node = Node(parameter.data)
            for indices, values in node.traverse():
            
                # check that indices are elements of sets (or are themselves
                #   sets) that have been defined
                if isinstance(parameter.data, dict):
                    for i in xrange(parameter.ndim):
                        index = indices[i]
                        if index not in data: # skip indices that are sets
                            indexSet = data[parameter.indices[i]].get(
                                run, data[parameter.indices[i]][defRun]
                            )
                            setElements = indexSet.data
                            if index not in indexSet.data:
                                msg = ''.join((
                                    'Supplied index \'%s\' for run ' % index,
                                    '%s, symbol \'%s\', but ' % (str(run), pName),
                                    '\'%s\' is not a member of \'%s\'.' % (index, indexSet.name)
                                ))
                                raise ValueError(msg)
                
                # for parameters with multiple values, add each record
                #   individually
                if isinstance(values, (list, tuple, set)):
                
                    # for one-dimensional parameters (Sets only)
                    if (parameter.ndim == 1) and isinstance(parameter, Set):
                        for v in values:
                            dbVars[parameter.name].add_record(v)
                    
                    # for multi-dimensional Sets and Parameters
                    else:
                    
                        # get the individual indices for the set over which records
                        #   have been defined
                        for i in xrange(len(indices)):
                            index = indices[i]
                            if index in data:
                                if run == -1: indexParameter = data[index][defRun]
                                else:
                                    try: indexParameter = data[index][run]
                                    except KeyError: indexParameter = data[index][defRun]
                                break
                                
                        # add values individually
                        for j in xrange(len(values)):
                            
                            # define the set of indices specific to this entry
                            index = indexParameter.data[j]
                            valueIndices = [x for x in indices]
                            valueIndices[i] = index
                            
                            # add the entry to the database
                            v = values[j]
                            if isinstance(parameter, Set):
                                dbVars[parameter.name].add_record(valueIndices[:-1] + [v])
                            else:
                                dbVars[parameter.name].add_record(valueIndices).value = v

                # for Sets not fitting in above
                elif isinstance(parameter, Set):
                
                    # 1-dimensional Sets where the set elements are defined as
                    #   values, but only a single element was given
                    if parameter.ndim == 1:
                        dbVars[parameter.name].add_record(values)
                        
                    # Sets with multiple dimensions and explicit indices that
                    #   dont have multiple values
                    else:
                        dbVars[parameter.name].add_record(indices)
                                
                # for zero-dimensional parameters for which we add a single
                #   value
                elif parameter.ndim == 0:
                    dbVars[parameter.name].add_record().value = values
                    
                # for 1+ dimensional values that are explicitly indexed
                else:
                    dbVars[parameter.name].add_record(indices).value = values
                    
        
        # add empty parameters for data not supplied by the user
        if parameters is not None:
            for pName in parameters:
                parameter = parameters[pName]
                if parameter.external and (parameter.loadname not in dbVars):
                    if isinstance(parameter, Set): 
                        dbVars[pName] = database.add_set(parameter.loadname, parameter.ndim)
                    elif isinstance(parameter, (Parameter, Scalar)): 
                        dbVars[pName] = database.add_parameter(parameter.loadname, parameter.ndim)
            
                    
        # write the gdx for this run    
        if run == -1: outname = os.path.join(outputDirectory, defGDXName)
        else: outname = os.path.join(outputDirectory, '%s%i' % (runGDXPref, run))
        try: database.export(outname)
        except: 
            print 'Unable to create GDX file %s' % outname
            
        if zip:
        
            # compress to zip
            outfile = outname + MAK_ZIP
            outgdx = outname + MAK_GDX
            zh = zipfile.ZipFile(outfile, "w")
            zh.write(outgdx, os.path.basename(outgdx), zipfile.ZIP_DEFLATED)
            zh.close()
            
            # delete the gdx
            try: os.remove(outgdx)
            except: print 'WARNING: Could not delete %s.' % outgdx
        
        else: outfile = outname + MAK_GDX
        print 'Completed %s...' % outname
        outfiles.append(outfile)
        
        # try to clear up some memory
        database.clear()
        del database, workspace
        
        
    return outfiles
    
    
if __name__ == '__main__':

    # module imports
    import os
    
    # input files and params (assumed to be in the same directory as this script)
    thisFolder = os.path.dirname(os.path.abspath(__file__))
    gmsFile = os.path.join(thisFolder, 'Habitat_Opt.gms')
    tableFile = os.path.join(thisFolder, r'test_data\table.csv')
    defFile = os.path.join(thisFolder, r'test_data\definitions.csv')
    outFolder = os.path.join(thisFolder, 'test_data')
    candidateColumns = ('can remove', 'can treat')
    bidColumn = 'BID'
    dsidColumn = 'DSID'
    
    # load the gams parameter definitions from the gams model file
    gamsParameters = read_gms(gmsFile)
    
    # prune barrier rows in the table file that wont make a difference in any
    #   optimization runs (i.e. that arent part of the network of candidates)
    tableDir, tableName = os.path.split(tableFile)
    tempTable = os.path.join(tableDir, '_' + tableName)
    try: 
        _ = prune_barriers(
            tableFile, tempTable, bidColumn, dsidColumn, 
            candidate_columns=candidateColumns
        )
    
        # load the data from tables and definitions file
        data = load_data(tempTable, defFile, gamsParameters)
        
        # make the gdx's for every model run
        print '\n'.join(make_gdx(data, outFolder, parameters=gamsParameters))
        
    finally:
        try: os.remove(tempTable)
        except:
            print 'Could not delete temporary pruned data %s' % tempTable
