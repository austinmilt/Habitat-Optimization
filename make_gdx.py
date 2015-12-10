### DOCUMENTATION

def main():
    # see Fishwerks_Opt_Inv_v4.gms for descriptions
    
    import csv, gams
    
    # ~~ VARIABLE AND COLUMN NAME DECLARATIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # GAMS model variables/parameters
    currentHab = 'maxBenefit'
    basePEff = 'basePropEfficiency'
    baseSEff = 'baseSingleEfficiency'
    projectPEff = 'projPropEfficiency'
    projectSEff = 'projSingleEfficiency'
    barriers = 'Barriers'
    goals = 'Goals'
    budget = 'budget'
    caps = 'cap'
    costs = 'projectCost'
    downstream = 'Downstream'
    projects = 'Projects'
    weight = 'weight'
    dummy = 'Dummy'
    
    # excel CSV columns (more below in column mapping section)
    barrierIDName = 'BID' # csv column name for Barriers set 
    downstreamIDName = 'DSID' # csv column name for down-stream ID D(J)
    removalCostName = 'COST' # csv column name for cR(J)
    lampCostName = 'LAMPCOST' # csv column name for lampricide treatment cH(J)
    
    

    # ~~ PARAMETER AND SET DEFINITIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    b = 5e5
    Goals = ['Fish1', 'Fish2', 'Fish3', 'Lamprey']
    capT = {'Fish1': 0, 'Fish2': 0, 'Fish3': 0, 'Lamprey': float('inf')}
    weightT = {'Fish1': 1, 'Fish2': 1, 'Fish3': 1, 'Lamprey': -1e-3}
    removalName = 'remove' # barrier removal project
    lampricideName = 'lampricide' # lampricide application project
    projectNames = (removalName, lampricideName)
    lampricideEfficiency = -0.95 # proportion of lamprey increased by lampricide (negative values reduce lamprey)
    dummyBarrierName = 'DUMMYBARRIER'
    
    # dataFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Test Results\barriers.csv'
    dataFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\OHanley Test\Catchment624777.csv'
    outputFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\data.gdx'
    
    # mapping from project names to project costs
    project2Cost = {
        lampricideName: lampCostName, removalName: removalCostName
    }
    
    
    # ~~ EXCEL COLUMN MAPPINGS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # mapping for target species to their column definitions in the csv
    #   Level 1: Target Names
    #       Level 2: Parameter Name and Column Name
    targetMap = {
        'Fish1': {
            currentHab: 'USHAB1',
            basePEff: 'PASS04',
            projectPEff: 'DELTAPASS1'
        },
        
        'Fish2': {
            currentHab: 'USHAB2',
            basePEff: 'PASS07',
            projectPEff: 'DELTAPASS2'
        },
        
        'Fish3': {
            currentHab: 'USHAB3',
            basePEff: 'PASS10',
            projectPEff: 'DELTAPASS3'
        },
        
        'Lamprey': {
            currentHab: 'USHAB4',
            basePEff: 'PASS_LAMP',
            projectPEff: 'DELTAPASS4'
        }
    }
    
    # column data types
    col2Type = {
        barrierIDName: str, downstreamIDName: str, removalCostName: float, 
        lampCostName: float
    }
    for target in targetMap:
        col2Type.update(dict((v, float) for v in targetMap[target].values()))
    
    
    
    # ~~ READ CSV ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    csvH = csv.reader(open(dataFile, 'r'))
    columns = csvH.next()
    nCol = len(columns)
    
    # get column indices in the csv that should be kept and exported
    keepCols = set([i for i in xrange(nCol) if columns[i] in col2Type])
    
    # get mapping from column name to index in processed data array
    cI = {}
    i = 0
    for c in columns:
        if c in col2Type:
            cI[c] = i
            i += 1
    
    data = []
    for inRow in csvH:
    
        # add each element to the output array in its final format if that
        #   column is meant to be added to the output (as defined in col2Type)
        outRow = [col2Type[columns[i]](inRow[i]) for i in xrange(nCol) if i in keepCols]
        data.append(outRow)
        
        
    # ~~ MAKE GDX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    workspace = gams.GamsWorkspace()
    database = workspace.add_database()
    
    # declarations
    dbVars = {
        budget: database.add_parameter(budget, 0),
        currentHab: database.add_parameter(currentHab, 2),
        basePEff: database.add_parameter(basePEff, 2),
        baseSEff: database.add_parameter(baseSEff, 2),
        projectPEff: database.add_parameter(projectPEff, 3),
        projectSEff: database.add_parameter(projectSEff, 3),
        barriers: database.add_set(barriers, 1),
        goals: database.add_set(goals, 1),
        caps: database.add_parameter(caps, 1),
        costs: database.add_parameter(costs, 2),
        downstream: database.add_set(downstream, 2),
        weight: database.add_parameter(weight, 1),
        projects: database.add_parameter(projects, 1),
        dummy: database.add_parameter(dummy, 1)
    }
    
    # simple definitions
    dbVars[budget].add_record().value = b
    dbVars[dummy].add_record(dummyBarrierName)
    for x in Goals: dbVars[goals].add_record(x)
    for x in capT: dbVars[caps].add_record(x).value = capT[x]
    for x in weightT: dbVars[weight].add_record(x).value = weightT[x]
    for x in projectNames: dbVars[projects].add_record(x)
    
    # definitions coming from rows of data[]
    for row in data:
        
        barrierID = row[cI[barrierIDName]]
        dbVars[barriers].add_record(barrierID)
        
        if row[cI[downstreamIDName]] == '-1': # self is root
            dbVars[downstream].add_record((barrierID, dummyBarrierName))
            
        else: # has a downstream node
            dbVars[downstream].add_record((barrierID, row[cI[downstreamIDName]]))
            
        for t in Goals:
            dbVars[currentHab].add_record((t, barrierID)).value = row[cI[targetMap[t][currentHab]]]
            dbVars[basePEff].add_record((t, barrierID)).value = row[cI[targetMap[t][basePEff]]]
            dbVars[baseSEff].add_record((t, barrierID)).value = 0
            dbVars[projectPEff].add_record((t, barrierID, removalName)).value = row[cI[targetMap[t][projectPEff]]]
            dbVars[projectSEff].add_record((t, barrierID, removalName)).value = 0
            
            # define effect of lampricide on fishes (0 for everythnig but lamprey)
            if t == 'Lamprey': efficiency = lampricideEfficiency
            else: efficiency = 0
            dbVars[projectSEff].add_record((t, barrierID, lampricideName)).value = efficiency
            dbVars[projectPEff].add_record((t, barrierID, lampricideName)).value = 0
            
        for v in projectNames:
            dbVars[costs].add_record((barrierID, v)).value = row[cI[project2Cost[v]]]
        
        
    database.export(outputFile)
    
    
if __name__ == '__main__':
    print main()
