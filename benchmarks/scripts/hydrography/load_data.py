# This file contains dataset-specific loading functions to facilitate
#   hydrography creation via hydrography.create_hydrography()

# Created 12/01/2015
# Updated 12/01/2015
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8

# load_data()
LOD_DAT_BAR = 'barriers'
LOD_DAT_RSX = 'RSX'
LOD_DAT_DAM = 'dams_flowlines'
LOD_DAT_FLO = 'flowlines'
LOD_DAT_CAT = 'catchments'
LOD_DAT_TRB = 'tributaries'
LOD_FLD_BID = 'BID'
LOD_FLD_BDS = 'BID_DS'
LOD_FLD_RID = 'RID'
LOD_FLD_NAT = 'NATION'
LOD_FLD_LAK = 'LAKE'
LOD_FLD_FPR = 'F_PROP'
LOD_FLD_HAB = 'HAB_UP'
LOD_FLD_CST = 'COST'
LOD_FLD_LAM = 'lamp_oid'
LOD_FLD_P04 = 'PASS04'
LOD_FLD_P07 = 'PASS07'
LOD_FLD_P10 = 'PASS10'
LOD_FLD_BFW = 'BANKFULL'
LOD_FLD_DRP = 'DROP'
LOD_FLD_HIT = 'HEIGHT'
LOD_FLD_RDS = 'RID_DS'
LOD_FLD_TID = 'TID'
LOD_FLD_CAT = 'HydroID'
LOD_FLD_CDS = 'HydroID_DS'
LOD_FLD_WSA = 'WSAKM2'
LOD_FLD_LEN = 'Shape_Length'
LOD_FLD_STO = 'STRAHLER'
LOD_VAL_SLF = -1

# ~~ load_hydro_mdb() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def load_hydro_mdb(database, **options):
    """
    LOAD_HYDRO_MDB() loads hydrography data from an mdb Access database using 
    arcpy and converts it into the format for create_hydrography().
    
    INPUT:
        database    = path to database file
        
        **options   = optional keyword arguments. Value arguments are:
        
            barriers: name of the barriers dataset in the database. Default is
                LOD_DAT_BAR
            rsx: name of the RSX dataset in the database. Default is 
                LOD_DAT_RSX
            dams: name of the dams dataset in the database: Default is 
                LOD_DAT_DAM
            flowlines: name of the flowlines dataset in the database. Default
                LOD_DAT_FLO
            catchments: name of the catchments dataset in the database. Default
                is LOD_DAT_CAT
            tributaries: name of the tributaries dataset in the database.
                Default is LOD_DAT_TRB
            bid_field: unique barrier ID field in barriers dataset. Default is
                LOD_FLD_BID
            bds_field: barrier downstream ID field in barriers dataset. Default
                is LOD_FLD_BDS
            rid_field: flowline ID field in barriers and flowlines dataset. 
                Default is LOD_FLD_RID
            nat_field: country of location of barrier in barriers dataset.
                Default is LOD_FLD_NAT
            fpr_field: proportion along flowline field in barriers dataset.
                Default is LOD_FLD_FPR
            hab_field: upstream habitat field in barriers dataset. Default is
                LOD_FLD_HAB
            cst_field: cost of barrier removal field in barriers dataset.
                Default is LOD_FLD_CST
            lam_field: lamprey first barrier ID field in barriers dataset.
                Default is LOD_FLD_LAM
            low_field: low-passability field in barriers dataset. Default is
                LOD_FLD_P04
            mid_field: mid-passability field in barriers dataset. Default is
                LOD_FLD_P07    
            hih_field: high-passability field in barriers dataset. Default is
                LOD_FLD_P10
            bfw_field: bankfull width field in the RSX dataset. Default is
                LOD_FLD_BFW
            drp_field: culvert drop height in the RSX dataset. Default is
                LOD_FLD_DRP
            hit_field: dam height field in the dams dataset. Default is
                LOD_FLD_HIT
            rds_field: flowline ID field of next downstream flowline in 
                flowlines dataset. Default is LOD_FLD_RDS
            tid_field: tributary ID field in flowlines and tributaries dataset.
                Default is LOD_FLD_TID
            cat_field: catchment ID field in flowlines and catchments dataset. 
                Default is LOD_FLD_CAT
            cds_field: catchment downstream ID field in catchments dataset.
                Default is LOD_FLD_CDS
            len_field: flowline's length field in flowlines dataset. Default
                is LOD_FLD_LEN
            sto_field: flowline's stream order field in flowlines dataset.
                Default is LOD_FLD_STO
            wsa_field: catchment's area field in catchments dataset. Default
                is LOD_FLD_WSA
            lak_field: lake into which tributary flows in tributaries dataset. 
                Default is LOD_FLD_LAK
            slf_value: value that indicates the downstream barrier, flowline,
                or catchment is itself. Default is LOD_VAL_SLF
                
    OUTPUT: a dictionary formatted for create_hydrography()
    """
    
    # imports
    from hydrography import (
        CRH_DAT_BAR, CRH_DAT_FLO, CRH_DAT_CAT, CRH_DAT_TRB, CRH_FLD_BID,
        CRH_FLD_BDS, CRH_FLD_RID, CRH_FLD_NAT, CRH_FLD_LAK, CRH_FLD_FPR, 
        CRH_FLD_HAB, CRH_FLD_CST, CRH_FLD_LAM, CRH_FLD_P04, CRH_FLD_P07, 
        CRH_FLD_P10, CRH_FLD_BFW, CRH_FLD_DRP, CRH_FLD_HIT, CRH_FLD_WID, 
        CRH_FLD_BLN, CRH_FLD_TYP, CRH_FLD_RDS, CRH_FLD_TID, CRH_FLD_CAT, 
        CRH_FLD_CDS, CRH_FLD_WSA, CRH_FLD_LEN, CRH_FLD_STO
    )
    
    import arcpy, os
    
    # update options
    P = {
        'barriers': LOD_DAT_BAR, 'flowlines': LOD_DAT_FLO,
        'catchments': LOD_DAT_CAT, 'tributaries': LOD_DAT_TRB, 
        'rsx': LOD_DAT_RSX, 'dams': LOD_DAT_DAM,
        'bid_field': LOD_FLD_BID, 'bds_field': LOD_FLD_BDS,
        'rid_field': LOD_FLD_RID, 'nat_field': LOD_FLD_NAT,
        'fpr_field': LOD_FLD_FPR, 'hab_field': LOD_FLD_HAB,
        'cst_field': LOD_FLD_CST, 'lam_field': LOD_FLD_LAM,
        'low_field': LOD_FLD_P04, 'mid_field': LOD_FLD_P07,
        'hih_field': LOD_FLD_P10, 'bfw_field': LOD_FLD_BFW,
        'drp_field': LOD_FLD_DRP, 'rds_field': LOD_FLD_RDS,
        'tid_field': LOD_FLD_TID, 'cat_field': LOD_FLD_CAT,
        'len_field': LOD_FLD_LEN, 'sto_field': LOD_FLD_STO,
        'wsa_field': LOD_FLD_WSA, 'lak_field': LOD_FLD_LAK,
        'cds_field': LOD_FLD_CDS, 'slf_value': LOD_VAL_SLF,
        'hit_field': LOD_FLD_HIT
        
    }
    for k in options: P[k.lower()] = options[k]
    
    
    # ~~ DEFINE CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # define datasets for loading
    datasets = {
        'barriers': os.path.join(database, P['barriers']),
        'rsx': os.path.join(database, P['rsx']),
        'dams': os.path.join(database, P['dams']),
        'flowlines': os.path.join(database, P['flowlines']),
        'catchments': os.path.join(database, P['catchments']),
        'tributaries': os.path.join(database, P['tributaries'])
    }
    
    # define fields to load for each dataset
    fields = {
        'barriers': (
            'bid_field', 'bds_field', 'rid_field', 'fpr_field', 'hab_field',
            'cst_field', 'nat_field', 'lam_field', 'low_field', 'mid_field',
            'hih_field'
        ),
        'rsx': ('bid_field', 'drp_field', 'bfw_field'),
        'dams': ('bid_field', 'hit_field',),
        'flowlines': (
            'rid_field', 'rds_field', 'tid_field', 'cat_field', 'len_field',
            'sto_field'
        ),
        'catchments': ('cat_field', 'cds_field', 'wsa_field'),
        'tributaries': ('tid_field', 'lak_field')
    }
    
    # define fields for which values should be mapped to other values
    val2Val = {
        'barriers': {'bds_field': (P['slf_value'], None)},
        'flowlines': {'rds_field': (P['slf_value'], None)},
        'catchments': {'cds_field': (P['slf_value'], None)}
    }
    
    # mapping from this dataset's fields to the formatted fields for 
    #   create_hydrography()
    fmap = {
        'barriers': (
            CRH_DAT_BAR, {
                'bid_field': CRH_FLD_BID, 'bds_field': CRH_FLD_BDS,
                'rid_field': CRH_FLD_RID, 'fpr_field': CRH_FLD_FPR,
                'hab_field': CRH_FLD_HAB, 'cst_field': CRH_FLD_CST,
                'nat_field': CRH_FLD_NAT, 'lam_field': CRH_FLD_LAM,
                'low_field': CRH_FLD_P04, 'mid_field': CRH_FLD_P07,
                'hih_field': CRH_FLD_P10, 'bfw_field': CRH_FLD_BFW,
                'drp_field': CRH_FLD_DRP, 'hit_field': CRH_FLD_HIT
            }
        ),
        'rsx': ( # placeholders to keep code from breaking
            'rsx', {
                'bid_field': 'bid_field', 'bfw_field': 'bfw_field', 
                'drp_field': 'drp_field'
            }
        ), 
        'dams': ( # placeholders to keep code from breaking
            'dams', {
            'bid_field': 'bid_field', 'hit_field': 'hit_field'
            }
        ), 
        'flowlines': (
            CRH_DAT_FLO, {
                'rid_field': CRH_FLD_RID, 'rds_field': CRH_FLD_RDS,
                'tid_field': CRH_FLD_TID, 'cat_field': CRH_FLD_CAT,
                'len_field': CRH_FLD_LEN, 'sto_field': CRH_FLD_STO
            }
        ),
        'catchments': (
            CRH_DAT_CAT, 
            {
                'cat_field': CRH_FLD_CAT, 'cds_field': CRH_FLD_CDS,
                'wsa_field': CRH_FLD_WSA
            }
        ),
        'tributaries': (
            CRH_DAT_TRB, 
            {'tid_field': CRH_FLD_TID, 'lak_field': CRH_FLD_LAK}
        )
    }
        
     
    # ~~ DEFINE SUB-DATA FOR PROCESSING DATA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # mapping from loaded raw value to formatted value
    def map_value(dataset, field, value):
        if (dataset in val2Val) and (field in val2Val[dataset]) and (value == val2Val[dataset][field][0]):
            return val2Val[dataset][field][1]
        else:
            return value
            
    # track index number in data for each field in the loaded data to
    #   make it easy to refer to data in processing in later steps
    fInd = {}
    for k in fields:
        fInd[k] = dict((fmap[k][1][fields[k][i]], i) for i in xrange(len(fields[k])))
    
    # do the same for rsx and dams, but adding onto barriers instead of 
    #   creating separate for roads and dams
    extraBarFields = ('rsx', 'dams')
    for k in extraBarFields:
        nBarField = len(fInd['barriers'])
        fInd['barriers'].update(
            dict(
                (fmap['barriers'][1][fields[k][i]], i+nBarField-1)
                for i in xrange(1, len(fields[k])) # skip bid field
            )
        )
    
    fInd['barriers'][CRH_FLD_TYP] = len(fInd['barriers'])
        
            
    # load data
    data = {}
    for datasetName in datasets:
        datasetPath = datasets[datasetName]
        datasetFields = [P[f] for f in fields[datasetName]]
        cursor = arcpy.da.SearchCursor(datasetPath, datasetFields)
        n = len(fields[datasetName])
        
        # load all rows at once, mapping values to new values where need-be
        #   and otherwise just taking the value as is
        data[fmap[datasetName][0]] = (
            fInd[datasetName],
            [
                [
                    map_value(
                        datasetName, fields[datasetName][i], row[i]
                    ) for i in xrange(n)
                ] for row in cursor
            ]
        )
            
        del cursor
        
    # append rsx and dam data on barrier data
    rowInds = {}
    for k in extraBarFields:
        dataTable = data[k][1]
        nRows = len(dataTable)
        idInd = data[k][0]['bid_field']
        rowInds[k] = dict((dataTable[i][idInd], i) for i in xrange(nRows))
    
    newBarName = fmap['barriers'][0]
    newBarIDName = fmap['barriers'][1]['bid_field']
    newBarIDInd = fInd['barriers'][newBarIDName]
    fieldLen = dict((k, len(fields[k])-1) for k in extraBarFields)
    for row in data[newBarName][1]:
        bid = row[newBarIDInd]
        isDam = False
        for k in extraBarFields:
        
            # add data from the rsx and dam datasets
            if bid in rowInds[k]:
                row.extend(data[k][1][rowInds[k][bid]][1:])
                if k == 'dams': isDam = True
                
            # populate with empty list to maintain size equality
            else:
                row.extend([None]*fieldLen[k])
                
        row.append(isDam)
        
    return data
