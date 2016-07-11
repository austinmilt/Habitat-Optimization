# This script prepares data for analysis, including exporting data from the
#   hydrography database, creation of the input tables for make_gdx.py, 
#   and creation of the gdx's for analysis

# Created 02/18/2016
# Updated 02/18/2016
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8

# ~~ GLOBAL CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# make_table()

# map_species_to_barriers()
MPB_DEF_SPP = None
MPB_DEF_CID = 'HydroID'
MPB_DEF_SPF = 'Species'
MPB_DEF_SKP = True
MPB_KWD_NSP = ''


# ~~ make_table() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def make_table(barriers, fields, outFile):
    """
    MAKE_TABLE() exports data from the hydrodatabase and calculates necessary
    derived fields not already in the database.
    
    INPUTS:
        barriers    = path to the barriers dataset within the hydrography
            database
            
        fields      = dict mapping for output fields from input fields, where
            keys are names of output fields and values are two-element list
            where first element is list of input fields and second element
            is function to process values in the input field rows.
            
        outFile     = path of CSV output file to create
        
    OUTPUTS:
        outFile, which is an Excel-style CSV to be processed by make_gdx.py
    """
    
    # imports
    import arcpy, csv
    
    # loop over the database file, getting data out and adding derived data
    #   for the output
    data = []
    outFields = fields.keys()
    inFields = list(set().union(*[fields[k][0] for k in fields]))
    f2I = dict((inFields[i], i) for i in xrange(len(inFields)))
    with arcpy.da.SearchCursor(barriers, inFields) as cursor:
        for row in cursor: # each barrier
            data.append([])
            for outField in outFields: # each piece of info to output
                inFieldVals = [row[f2I[k]] for k in fields[outField][0]]
                outFieldVal = fields[outField][1](*inFieldVals)
                data[-1].append(outFieldVal)
                
    # write output and finish
    writer = csv.writer(open(outFile, 'wb'))
    writer.writerow(outFields)
    for row in data:
        writer.writerow(row)
    
    return outFile
    

    
# ~~ map_species_to_barriers() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def map_species_to_barriers(hydroObject, presenceData, **options):
    """
    MAP_SPECIES_TO_BARRIERS() finds the barriers above which each species
    of interest might be found if that barrier were removed
    
    INPUTS:
        hydroObject     = Hydrography object as returned by the hydrography
            module
        
        presenceData    = shapefile of species-by-catchment locations (as
            created/provided by TNC), where shapes are catchments and may
            be repeated, once for each species found in that catchment and
            only once if no (or one) species is there
            
        **options       = (optional) keyword arguments, including:
            spp_names: list of names of species to include
                in the output from [presenceData]. If None, all species
                are included. Default is MPB_DEF_SPP (see top of script)
            
            spp_field: name of the field in [presenceData] that lists the
                name of a species found in a catchment. Default is MPB_DEF_SPF

            cid_field: name of the field in [presenceData] with a catchment's
                ID. Default is MPB_DEF_CID
                
            skip_blanks: boolean indicating to skip blank species (i.e. exclude
                catchments with no species in it). Default is MPB_DEF_SKP
            
    OUTPUTS:
        dictionary where keys are barrier IDs and values are lists of species
        expected to be found above that barrier if it were removed (i.e. the
        barrier is in a tributary network where the species is found)
    """
    
    # imports
    import arcpy, csv
    
    # update options with user preferences
    P = {
        'spp_names': MPB_DEF_SPP, 'cid_field': MPB_DEF_CID, 
        'spp_field': MPB_DEF_SPF, 'skip_blanks': MPB_DEF_SKP
    }
    for k in options: P[k.lower()] = options[k]
    
    # get list of species in each catchment
    spp2tid = {}
    cid2tid = dict((c.id, c.tributary.id) for c in hydroObject.get_catchments())
    for cid, species in arcpy.da.SearchCursor(presenceData, [P['cid_field'], P['spp_field']]):
        tid = cid2tid.get(cid, None)
        if tid is None: continue
        if tid not in spp2tid: spp2tid[tid] = set()
        species = species.strip()
        if P['skip_blanks'] and (species == MPB_KWD_NSP): continue
        if (P['spp_names'] is not None) and (species not in P['spp_names']): continue
        spp2tid[tid].add(species)
    
    # map species to barriers
    bid2spp = dict((b.id, spp2tid.get(b.reach.tributary.id, set())) for b in hydroObject.get_barriers())

    return bid2spp

    
  
def main():
    
    # ~~ IMPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    from make_gdx import make_gdx, read_gms, load_data, prune_barriers
    from hydrography.hydrography import Hydrography
    from hydrography.load_data import load_hydro_mdb
    import os
    
    
    
    # ~~ DEFINE INPUTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # input files
    barriers = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\raw_data\GL_pruned_hydrography.mdb\barriers'
    tableCSV = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\benchmarks\data\table.csv'
    defFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\benchmarks\data\definitions.csv'
    gmsFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\benchmarks\scripts\Habitat_Opt.gms'
    outFolder = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\benchmarks\data\gdxs'
    hydroMDB = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\raw_data\GL_pruned_hydrography.mdb'
    sppData = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\raw_data\Catchments_with_FishPresence_Updated_4-25-2016\catchments_w_fish_presence_4-25-2016.shp'
    
    # other parameters
    bidColumn = 'BID'
    dsidColumn = 'BID_DS'
    
    # get hydrography to map from bids to species presence
    hydrodata = load_hydro_mdb(hydroMDB)
    hydrography = Hydrography(hydrodata)
    
    # assess which species might use which sections above which barriers
    #   (i.e. if that species is found in the river network of the barrier)
    bid2spp = map_species_to_barriers(hydrography, sppData)
    del hydrography, hydrodata
    def spp_hab(sid, bid, hab):
        if sid in bid2spp[bid]: return hab
        else: return 0.
    fish1_hab = lambda b,h: spp_hab('Esox lucius', b, h)
    fish2_hab = lambda b,h: spp_hab('Moxostoma anisurum', b, h)
    fish3_hab = lambda b,h: spp_hab('Acipenser fulvescens', b, h)
    lamp_hab = lambda b,h: spp_hab('Petromyzon marinus', b, h)
    
    # mapping from hydrography database fields to output fields for gams model
    fields = {
        'bid': ([bidColumn], lambda s: long(float(s))),
        'dsid': ([dsidColumn], lambda s: long(float(s))),
        'hab_fish1': ([bidColumn, 'HAB_UP'], fish1_hab),
        'hab_fish2': ([bidColumn, 'HAB_UP'], fish2_hab),
        'hab_fish3': ([bidColumn, 'HAB_UP'], fish3_hab),
        'hab_lamprey': ([bidColumn, 'HAB_UP'], lamp_hab),
        'pass_fish1': (['PASS04'], lambda s: s), # swimming guilds from Allison's paper
        'pass_fish2': (['PASS07'], lambda s: s),
        'pass_fish3': (['PASS10'], lambda s: s),
        'pass_lamprey': (['PASS07'], lambda s: s),
        'cost': (['COST'], lambda s: s),
        'is_root': ([dsidColumn], lambda s: {-1: 1}.get(int(float(s)), 0)),
        'candidate': ([], lambda: 1),
        'passchange_fish1': (['PASS04'], lambda s: 1-float(s)),
        'passchange_fish2': (['PASS07'], lambda s: 1-float(s)),
        'passchange_fish3': (['PASS10'], lambda s: 1-float(s)),
        'passchange_lamprey': (['PASS07'], lambda s: 1-float(s)),
        'habchange_lamprey':([bidColumn, 'HAB_UP'], lambda b,h: -0.95*lamp_hab(b,h))
    }
    

    # ~~ CREATE GDX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    
    
    # make table.csv
    make_table(barriers, fields, tableCSV)
    
    # load the gams parameter definitions from the gams model file
    gamsParameters = read_gms(gmsFile)
    
    # load the data from tables and definitions file
    data = load_data(tableCSV, defFile, gamsParameters)
        
    # make the gdx's for every model run
    print '\n'.join(make_gdx(
        data, outFolder, parameters=gamsParameters, zip=False
    ))
    
    
if __name__ == '__main__':
    print main()
    