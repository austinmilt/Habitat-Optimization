### DOCUMENTATION

def main():
    # see Habitat_Opt.gms for descriptions
    
    import csv, gams
    
    # ~~ VARIABLE AND COLUMN NAME DECLARATIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # GAMS model variables/parameters
    benefitMaxBase = 'benefitMaxBase'
    benefitMaxChange = 'benefitMaxChange'
    passBase = 'passBase'
    passChange = 'passChange'
    barriers = 'Barriers'
    roots = 'Root'
    goals = 'Targets'
    beneficiaries = 'TargetsBeneficiary'
    controls = 'TargetsControl'
    budget = 'budget'
    caps = 'cap'
    costs = 'cost'
    downstream = 'Downstream'
    projects = 'Projects'
    projectsPass = 'ProjectsPassability'
    projectsBen = 'ProjectsBenefit'
    weight = 'weight'
    # dummy = 'Dummy'
    
    # excel CSV columns (more below in column mapping section)
    barrierIDName = 'BID' # csv column name for Barriers set 
    downstreamIDName = 'DSID' # csv column name for down-stream ID D(J)
    removalCostName = 'COST' # csv column name for cR(J)
    lampCostName = 'HABCOST' # csv column name for lampricide treatment cH(J)
    
    

    # ~~ PARAMETER AND SET DEFINITIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    b = 5e5
    Targets = ['Fish1', 'Fish2', 'Fish3', 'Lamprey']
    beneficiariesT = ['Fish1', 'Fish2', 'Fish3']
    controlsT = ['Lamprey']
    capT = {'Fish1': 0, 'Fish2': 0, 'Fish3': 0, 'Lamprey': float('inf')}
    weightT = {'Fish1': 1, 'Fish2': 1, 'Fish3': 1, 'Lamprey': -1}
    removalName = 'remove' # barrier removal project
    lampricideName = 'lampricide' # lampricide application project
    projectTypes = {removalName: projectsPass, lampricideName: projectsBen}
    lampricideEfficiency = -0.95 # proportion of lamprey increased by lampricide (negative values reduce lamprey)
    # dummyBarrierName = 'DUMMYBARRIER'
    
    # dataFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Test Results\barriers.csv'
    dataFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\OHanley Generic\OPL code\Catchment624777.csv'
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
            benefitMaxBase: 'USHAB1',
            passBase: 'PASS04',
            passChange: 'DELTAPASS1',
            benefitMaxChange: 'DELTAHAB1'
        },
        
        'Fish2': {
            benefitMaxBase: 'USHAB2',
            passBase: 'PASS07',
            passChange: 'DELTAPASS2',
            benefitMaxChange: 'DELTAHAB2'
        },
        
        'Fish3': {
            benefitMaxBase: 'USHAB3',
            passBase: 'PASS10',
            passChange: 'DELTAPASS3',
            benefitMaxChange: 'DELTAHAB3'
        },
        
        'Lamprey': {
            benefitMaxBase: 'USHAB4',
            passBase: 'PASS_LAMP',
            passChange: 'DELTAPASS4',
            benefitMaxChange: 'DELTAHAB4'
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
        benefitMaxBase: database.add_parameter(benefitMaxBase, 2),
        benefitMaxChange: database.add_parameter(benefitMaxChange, 3),
        passBase: database.add_parameter(passBase, 2),
        passChange: database.add_parameter(passChange, 3),
        barriers: database.add_set(barriers, 1),
        roots: database.add_set(roots, 1),
        goals: database.add_set(goals, 1),
        beneficiaries: database.add_set(beneficiaries, 1),
        controls: database.add_set(controls, 1),
        caps: database.add_parameter(caps, 1),
        costs: database.add_parameter(costs, 2),
        downstream: database.add_set(downstream, 2),
        weight: database.add_parameter(weight, 1),
        projects: database.add_parameter(projects, 1),
        projectsPass: database.add_parameter(projectsPass, 1),
        projectsBen: database.add_parameter(projectsBen, 1),
        # dummy: database.add_parameter(dummy, 1)
    }
    
    # simple definitions
    dbVars[budget].add_record().value = b
    # dbVars[dummy].add_record(dummyBarrierName)
    # dbVars[barriers].add_record(dummyBarrierName)
    for x in Targets: dbVars[goals].add_record(x)
    for x in beneficiariesT: dbVars[beneficiaries].add_record(x)
    for x in controlsT: dbVars[controls].add_record(x)
    for x in capT: dbVars[caps].add_record(x).value = capT[x]
    for x in weightT: dbVars[weight].add_record(x).value = weightT[x]
    for x in projectTypes:
        dbVars[projects].add_record(x)
        if projectTypes[x] == projectsPass: dbVars[projectsPass].add_record(x)
        elif projectTypes[x] == projectsBen: dbVars[projectsBen].add_record(x)
    
    # definitions coming from rows of data[]
    for row in data:
        
        barrierID = row[cI[barrierIDName]]
        dbVars[barriers].add_record(barrierID)
        dbVars[benefitMaxChange].add_record((barrierID, lampricideName, 'Lamprey')).value = row[cI[targetMap['Lamprey'][benefitMaxChange]]]
        
        if row[cI[downstreamIDName]] == '-1': # self is root
            # dbVars[downstream].add_record((barrierID, dummyBarrierName))
            dbVars[roots].add_record(barrierID)
            
        else: # has a downstream node
            dbVars[downstream].add_record((barrierID, row[cI[downstreamIDName]]))
            
        for t in Targets:
            dbVars[benefitMaxBase].add_record((barrierID, t)).value = row[cI[targetMap[t][benefitMaxBase]]]
            dbVars[passBase].add_record((barrierID, t)).value = row[cI[targetMap[t][passBase]]]
            dbVars[passChange].add_record((barrierID, removalName, t)).value = row[cI[targetMap[t][passChange]]]
            
        for v in projectTypes:
            dbVars[costs].add_record((barrierID, v)).value = row[cI[project2Cost[v]]]
        
        
    database.export(outputFile)
    
    
if __name__ == '__main__':
    print main()
