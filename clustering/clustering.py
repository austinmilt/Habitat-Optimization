# Created 05/12/2016
# Updated 05/12/2016
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8
# Description:
#       This script's main purpose is to come up with clusters of species that
#   maximizes the amount of information about a species in its cluster and
#   minimize the number of clusters to do so.

# ~~ GLOBAL IMPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
import numpy


# ~~ CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
OPT_DEF_MSP = 0.01
OPT_DEF_MDS = 0.01
OPT_DEF_WSP = 1.0
OPT_DEF_WDS = 1.0
OPT_DEF_DCT = 1.0
OPT_DEF_GEN = 1000
OPT_DEF_POP = 20
OPT_DEF_IPP = 1000
OPT_DEF_CLS = 1
OPT_DEF_CRS = 0.7
OPT_DEF_MIG = 0.01
OPT_DEF_ELT = 0.1
OPT_DEF_KEP = 0.05
OPT_DEF_SCV = 0.0001


# ~~ Species ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Species:
    """
    Species class, with swim speed and ordered list of binary association to
    watersheds as inputs.
    """

    import numpy

    def __init__(self, speed, distribution, identity=None):
        self.speed = speed
        self.distribution = numpy.array(distribution, dtype=numpy.int8)
        self.speedError = None
        self.distroFit = None
        self.id = identity


    def __repr__(self):
        return 'Species <%s>' % str(self.id)

        
    def evaluate_cluster(self, clusters, **params):
        """Determines the cluster best suited for this species, and saves the fit to that cluster."""
        
        # calculate speed error
        speedErrors = [(self.speed - c.speed)**2 / params['norm_speed'] for c in clusters]
        
        # calculate distribution fit
        # distroFits = [distro_fit(self, c) / params['norm_distro'] for c in clusters]
        distroFits = [((1 - self.distribution - c.watersheds)**2).sum() / params['norm_distro'] for c in clusters]
        
        
        # calcualte partial objective for each cluster and get the best cluster
        objectives = [params['weight_distro']*distroFits[i] - params['weight_speed']*speedErrors[i] for i in xrange(len(clusters))]
        cluster = numpy.argmax(objectives)
        return (clusters[cluster], speedErrors[cluster], distroFits[cluster])
        

        
# ~~ Cluster ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Cluster:

    import numpy
    
    def __init__(self, speed, watersheds):
        self.speed = speed
        self.watersheds = numpy.array(watersheds, dtype=numpy.int8)
        
        
    def mutate(self, **params):
        """Mutates cluster by adjusting speed and watershed assignments"""
        
        # mutate speed
        self.speed += params['mutate_speed']*numpy.random.randint(-1,2)*numpy.random.rand()
        
        # mutate watershed by flipping assignment
        flip = numpy.random.rand(self.watersheds.size) < params['mutate_distro']
        self.watersheds[flip] *= -1
        self.watersheds[flip] += 1
        
        

# ~~ Individual ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Individual:
    
    def __init__(self, clusters, species):
        self.clusters = numpy.array(clusters)
        self.species = dict((s, None) for s in species)
        self.fitness = None
        
        
    def mutate(self, **params):
        """Mutates individual by adjusting cluster speeds and watershed assignments"""
        [c.mutate(**params) for c in self.clusters]
        
        
    def assign_species_to_clusters(self, **params):
        """Assigns species to clusters based on cluster attributes."""
        self.species = dict((s, s.evaluate_cluster(self.clusters, **params)) for s in self.species)
        
        
    def evaluate_fitness(self, **params):
        """Evaluates the fitness of an individual for a maximization"""
        S = self.species
        self.fitness = sum([S[s][2]*params['weight_distro'] - S[s][1]*params['weight_speed'] for s in S])
        return self.fitness
        
        
    def copy(self):
        """Makes a copy of self with attributes not shared in memory."""
        clusters = [Cluster(c.speed, c.watersheds) for c in self.clusters]
        return Individual(clusters, self.species)
        
        
    def summarize(self):
        C = self.clusters
        S = self.species
        ns = dict((c, len([s for s in S if S[s][0] is c])) for c in C)
        nw = dict((c, sum(c.watersheds)) for c in C)
        rows = ['Fitness: %f' % self.fitness]
        fmstr = 'Cluster %i: %i species, %i watersheds, speed = %0.2f'
        rows.extend([
            fmstr % (i, ns[C[i]], nw[C[i]], C[i].speed) for i in xrange(len(C))
        ])
        print '\n'.join(rows)
        
        
        
# ~~ Optimizer ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Optimizer:
    """Optimization class, pass in list of Species objects to initialize."""
    
    import numpy
    
    def __init__(self, species):
        self.population = None
        self.species = species
        self.maxSpeed = max([s.speed for s in species])
        self.minSpeed = min([s.speed for s in species])
        self.nSheds = len(species[0].distribution)
        self.nSpecies = len(species)
        self.normSpeed = sum([s.speed*s.speed for s in species])
        self.normDistro = float(self.nSheds * self.nSpecies)
        self.minDistroRate = min([sum(s.distribution) for s in species]) / float(self.nSheds)
        
        
    def make_random_individual(self, **params):
        """Makes a random individual."""
        speeds = (self.maxSpeed - self.minSpeed)*numpy.random.rand(params['n_clusters']) + self.minSpeed
        watersheds = [(numpy.random.rand(self.nSheds) < 0.5).astype(numpy.uint8) for i in xrange(params['n_clusters'])]
        clusters = [Cluster(speeds[i], watersheds[i]) for i in xrange(params['n_clusters'])]
        individual = Individual(clusters, self.species)
        individual.assign_species_to_clusters(**params)
        individual.evaluate_fitness(**params)
        return individual
        
        
    def initialize_population(self, **params):
        """
        Initializes population with some best individuals chosen from a random
        set.
        """
        candidates = numpy.array([self.make_random_individual(**params) for i in xrange(params['init_size'])])
        fitnesses = [c.fitness for c in candidates]
        return candidates[numpy.argsort(fitnesses)[::-1][:params['popsize']]]
        
        
    def optimize_clusters(self, **options):
        """
        OPTIMIZE_CLUSTERS() Determines optimal cluster parameters given a set
            clusters for species using a genetic algorithm
        
        INPUTS:
            **options    = (optional) keyword arguments, including:
                mutate_speed: mutation rate for cluster speed, 0-1.
                    Default is OPT_DEF_MSP
                    
                mutate_distro: mutation rate for cluster watersheds, 0-1.
                    Default is OPT_DEF_MDS
                    
                weight_speed: weight (after normalization) of speed error in
                    the objective. Default is OPT_DEF_WSP.
                    
                weight_distro: weight (after normalization) of distribution fit
                    in the objective. Default is OPT_DEF_WDS.
                    
                generations: number of generations to run. Default is 
                    OPT_DEF_GEN
                    
                popsize: number of individuals in each generation. Default is
                    OPT_DEF_POP
                    
                init_size: number of individuals to create in population
                    initialization. Default is OPT_DEF_IPP
                    
                n_clusters: number of clusters. Default is OPT_DEF_CLS
                
                norm_speed: normalization constant for speed (separate from
                    objective weight). Default is sum of square species speeds
                    
                norm_distro: normalization constant for distribution fit
                    (separate from objective weight). Default is product
                    of number of species and watersheds.
                    
                migration: rate at which an individual is crossed with a new
                    random individual instead of one from the current 
                    population. Default is OPT_DEF_MIG
                    
                crossrate: rate at which two individuals crossover instead of
                    taking all attributes from the more fit parent. Default is
                        OPT_DEF_CRS
                    
                elite: proportion of fittest individuals in each generation
                    kept without mutation for the next generation. Default
                    is OPT_DEF_ELT
                    
                keepworse: probability that an offspring worse than its
                    parents will be kept for the next generation anyway.
                    Default is OPT_DEF_KEP
                
                stopcv: coefficient of variation of fitnesses of population
                    at which convergence is assumed and the optimization
                    stops. Default is OPT_DEF_
                    
        OUTPUTS:
            best individual from the optimization. Access the solution in
            individual.species dictionary
        """
        
        # update defaults with user preferences
        params = {
            'mutate_speed': OPT_DEF_MSP, 'mutate_distro': OPT_DEF_MDS,
            'weight_speed': OPT_DEF_WSP, 'weight_distro': OPT_DEF_WDS,
            'generations': OPT_DEF_GEN, 'popsize': OPT_DEF_POP,
            'init_size': OPT_DEF_IPP, 'n_clusters': OPT_DEF_CLS,
            'norm_speed': self.normSpeed, 'norm_distro': self.normDistro,
            'migration': OPT_DEF_MIG, 'crossrate': OPT_DEF_CRS, 
            'elite': OPT_DEF_ELT, 'keepworse': OPT_DEF_KEP, 
            'stopcv': OPT_DEF_SCV
        }
        for k in options: params[k.lower()] = options[k]
        
        # define other constants
        mutSpdAbs = (self.maxSpeed - self.minSpeed)*params['mutate_speed']
        
        # initialize population
        nextGeneration = self.initialize_population(**params)
        
        # optimize
        population = numpy.empty(nextGeneration.size, object)
        ranks = numpy.empty(population.size, numpy.uint16)
        parentChoices = numpy.empty(population.size, numpy.uint16)
        nElite = int(round(params['elite']*population.size))
        g = 0
        while True:
        
            # update population statistics
            population[:] = nextGeneration[:]
            fitnesses = [i.fitness for i in population]
            fitOrder = numpy.argsort(fitnesses)
            print 'Generation %i. Best: %0.2f. Median: %0.2f' % (g, fitnesses[fitOrder[-1]], numpy.median(fitnesses))
            
            # retain elites
            nextGeneration[:nElite] = population[fitOrder[-nElite:]]
            
            # fill in the rest of the population
            filled = nElite
            ranks[fitOrder] = numpy.arange(population.size, dtype=numpy.uint16) + 1
            while filled < population.size:
            
                # choose two individuals to crossover (optionally from random 
                #   population) by biased random selection (fitter individuals more
                #   likely to be chosen)
                parent1, parent2 = population[
                    numpy.argsort(numpy.random.rand(population.size)*ranks)[-2:]
                ]
                if numpy.random.rand() < params['migration']:
                    parent2 = self.make_random_individual(**params)
                    
                # perform crossover with some probability. If crossover is
                #   done, randomly swap clusters from the two parents
                offspring = parent1.copy()
                if numpy.random.rand() < params['crossrate']:
                    crossClusters = numpy.random.rand(params['n_clusters']) < 0.5
                    offspring.clusters[crossClusters] = parent2.copy().clusters[crossClusters]
                
                # mutate offspring
                offspring.mutate(
                    mutate_speed=mutSpdAbs, 
                    mutate_distro=params['mutate_distro']
                )
                
                # evaluate offspring fitness
                offspring.assign_species_to_clusters(**params)
                offspring.evaluate_fitness(**params)
                
                # add individual to next generation with some probability
                if (offspring.fitness >= parent1.fitness) or (numpy.random.rand() < params['keepworse']):
                    nextGeneration[filled] = offspring
                    filled += 1

            # assess stopping criteria
            g += 1
            if g == params['generations']: break
            else:
                nextFitnesses = [i.fitness for i in nextGeneration]
                cv = numpy.std(nextFitnesses) / numpy.mean(nextFitnesses)
                if cv < params['stopcv']: break
            
                    
        # return the best individual
        return nextGeneration[numpy.argsort([i.fitness for i in nextGeneration])[-1]]
        
        
    def optimize_cluster_number(self, **options):
        """
        Determines both the optimal number of clusters and cluster parameters
        by maximizing species information contained in clusters and
        discounting for the number of clusters (parsimony).
        
        INPUTS:
            **options    = (optional) keyword arguments, including
                everything from optimize_clusters and
                
                discount: discount rate for the number of clusters. Default
                    is 1/[number of species]
                    
                weight_discount: weight that discount should have relative
                    to speed and distribution weights in determining
                    parsimony. Default is OPT_DEF_DCT
        """
        
        # update defaults with user preferences
        params = {'discount': 1./self.nSpecies, 'weight_discount': OPT_DEF_DCT}
        for k in options: params[k.lower()] = options[k]
        
        # incrementally increase the number of clusters and determine
        # the point at which the objective starts decreasing, then
        # take the previous solution
        previousScore = float('-inf')
        currentScore = float('-inf')
        previous = None
        current = None
        totWeight = params['weight_discount']*params['discount']
        for n in xrange(1,self.nSpecies+1):
            
            # determine stopping criteria
            if previousScore > currentScore: return previous
            
            # try the next cluster number
            previous = current
            previousScore = currentScore
            print 'CLUSTER NUMBER %i' % n
            current = self.optimize_clusters(n_clusters=n, **params)
            currentScore = current.fitness - totWeight*n
            
        return current
            
            
def extract_species_distributions(outfile):
    """
    Extracts species distribution data from TNC catchment data
    and writes to presence-absence matrix CSV
    """
    
    # imports
    import sys, arcpy, csv, numpy
    
    # input files
    hydroCodePath = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\analyses' # hydrogaphy code path
    hydroMDB = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\raw_data\GL_pruned_hydrography.mdb'
    sppData = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\Lamprey Cap Tradeoffs\raw_data\Catchments_with_FishPresence_Updated_4-25-2016\catchments_w_fish_presence_4-25-2016.shp'
    
    # other parameters
    cidField = 'HydroID'
    speciesField = 'Species'
    
    # import helper functions
    cPath = sys.path
    sys.path = [hydroCodePath] + cPath
    from hydrography.hydrography import Hydrography
    from hydrography.load_data import load_hydro_mdb
    
    # load hydrography data
    hydrodata = load_hydro_mdb(hydroMDB)
    hydrography = Hydrography(hydrodata)
    
    # load species trib data
    spp2tid = {}
    cid2tid = dict((c.id, c.tributary.id) for c in hydrography.get_catchments())
    tids = sorted(set(cid2tid.values()))
    ntid = len(tids)
    tid2ind = dict((tids[i], i) for i in xrange(ntid))
    for cid, species in arcpy.da.SearchCursor(sppData, [cidField, speciesField]):
        tid = cid2tid.get(cid, None)
        if tid is None: continue
        species = species.strip()
        if species == '': continue
        if species not in spp2tid: spp2tid[species] = numpy.zeros(len(tids), dtype=numpy.uint8)
        spp2tid[species][tid2ind[tid]] = 1

    # write species data to output csv
    species = sorted(spp2tid.keys())
    writer = csv.writer(open(outFile, 'wb'))
    header = [''] + tids
    writer.writerow(header)
    for s in species:
        row = [s] + list(spp2tid[s])
        writer.writerow(row)
        
    return outFile
    
    
    
def extract_species_speeds(outfile):
    """
    Extracts species speed information and writes to a csv. For now the table
    is embedded in the function and taken from Moody 2016.
    """
    
    # imports
    import csv
    
    # inputs
    header = ['Species', 'Speed (cm/s)', 'Guild']
    
    # get data
    speeds = {
        'Acipenser fulvescens': (100.0, 'Strong'), # Strong
        'Anguilla rostrata': (20.0, 'Weak'), # Weak
        'Aplodinotus grunniens': (70.0, 'Moderate'), # Moderate (Unknown)
        'Carpiodes cyprinus': (112.0, 'Strong'), # Strong
        'Catostomus catostomus': (62.0, 'Moderate'), # Moderate
        'Catostomus commersonii': (62.0, 'Moderate'), # Moderate
        'Coregonus artedii': (63.0, 'Moderate'), # Moderate
        'Coregonus clupeaformis': (57.0, 'Moderate'), # Moderate
        'Couesius plumbeus': (30.0, 'Weak'), # Weak
        'Cyprinus carpio': (112.0, 'Strong'), # Strong
        'Esox lucius': (30.0, 'Weak'), # Weak
        'Esox masquinongy': (64.0, 'Moderate'), # Moderate
        'Gymnocephalus cernuus': (40.0, 'Weak'), # Weak (Unknown)
        'Ichthyomyzon castaneus': (40.0, 'Weak'), # Weak (Unknown)
        'Ichthyomyzon fossor': (40.0, 'Weak'), # Weak (Unknown)
        'Ichthyomyzon unicuspis': (35.0, 'Weak'), # Weak
        'Ictalurus punctatus': (70.0, 'Moderate'), # Moderate (Unknown)
        'Ictiobus cyprinellus': (70.0, 'Moderate'), # Moderate (Unknown)
        'Ictiobus niger': (70.0, 'Moderate'), # Moderate (Unknown)
        'Lepisosteus osseus': (51.0, 'Moderate'), # Moderate
        'Lota lota': (39.0, 'Weak'), # Weak
        'Micropterus dolomieu': (81.0, 'Moderate'), # Moderate
        'Moxostoma anisurum': (70.0, 'Moderate'), # Moderate (Unknown)
        'Moxostoma macrolepidotum': (70.0, 'Moderate'), # Moderate (Unknown)
        'Moxostoma valenciennesi': (70.0, 'Moderate'), # Moderate (Unknown)
        'Neogobius melanostomus': (40.0, 'Weak'), # Weak (Unknown)
        'Notrophis hudsonius': (40.0, 'Weak'), # Weak (Unknown)
        'Notropis atherinoides': (40.0, 'Weak'), # Weak (Unknown)
        'Oncorhynchus gorbuscha': (100.0, 'Strong'), # Strong
        'Oncorhynchus kisutch': (640.0, 'Strong'), # Strong
        'Oncorhynchus mykiss': (440.0, 'Strong'), # Strong
        'Oncorhynchus tshawytscha': (304.0, 'Strong'), # Strong
        'Perca flavescens': (27.0, 'Weak'), # Weak
        'Percina copelandi': (40.0, 'Weak'), # Weak (Unknown)
        'Percina shumardi': (31.0, 'Weak'), # Weak
        'Percopsis omiscomaycus': (55.0, 'Weak'), # Weak
        'Petromyzon marinus': (79.0, 'Moderate'), # Moderate
        'Prosopium cylindraceum': (45.0, 'Weak'), # Weak
        'Rhinichthys cataractae': (62.0, 'Moderate'), # Moderate
        'Salvelinus fontinalis': (59.0, 'Moderate'), # Moderate
        'Salvelinus namaycush': (38.0, 'Weak'), # Weak
        'Sander canadense': (40.0, 'Weak'), # Weak (Unknown)
        'Sander vitreus': (73.0, 'Moderate') # Moderate
    }
        
    # write output
    writer = csv.writer(open(outfile, 'wb'))
    writer.writerow(header)
    for species in sorted(speeds.keys()):
        writer.writerow([species, speeds[species][0], speeds[species][1]])
        
    return outfile
    
    
        
def test():
    species = [
        Species(1., [0, 0, 0, 1, 1]), Species(1., [0, 0, 0, 1, 1]),
        Species(2., [1, 1, 1, 0, 0]), Species(2., [1, 1, 1, 0, 0]),
        Species(2., [1, 1, 1, 0, 0]), Species(2., [1, 1, 1, 0, 0])
    ]
    optimizer = Optimizer(species)
    best = optimizer.optimize_cluster_number()
    best.summarize()
    print best.clusters[0].watersheds
    print best.clusters[1].watersheds
    
    
    
if __name__ == '__main__':

    import csv, numpy

    # input files
    speedFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\clustering\speeds.csv'
    distFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\clustering\spp_x_trib.csv'
    resultsFile = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Lamprey Control\code\clustering\clusters_guild.csv'
    
    # extract species data
    # extract_species_distributions(distFile)
    # extract_species_speeds(speedFile)
    
    # load species data
    sfSppCol = 'Species'
    # sfSpdCol = 'Speed (cm/s)'
    sfSpdCol = 'Guild'
    # speed_func = lambda s: float(s)
    speed_func = lambda s: {'Strong': 1.0, 'Moderate': 0.7, 'Weak': 0.4}.get(s, None)
    
    reader = csv.reader(open(speedFile, 'r'))
    columns = reader.next()
    c2i = dict((columns[i], i) for i in xrange(len(columns)))
    speeds = dict((row[c2i[sfSppCol]], speed_func(row[c2i[sfSpdCol]])) for row in reader)
    
    reader = csv.reader(open(distFile, 'r'))
    watersheds = numpy.array(reader.next()[1:])
    distributions = dict((row[0], [int(r) for r in row[1:]]) for row in reader)

    # set up the inputs for the optimization
    species = []
    for s in speeds:
        if s in distributions:
            species.append(Species(speeds[s], distributions[s], s))
            
    # perform optimization
    optimizer = Optimizer(species)
    results = []
    for i in xrange(1, optimizer.nSpecies+1):
        print '# Clusters: %i ##########' % i
        results.append(optimizer.optimize_clusters(n_clusters=i, generations=5000))
    
    # write output
    writer = csv.writer(open(resultsFile, 'wb'))
    writer.writerow(['# Clusters', 'Cluster', 'Speed', 'Species', 'Watersheds'])
    for i in xrange(len(results)):
        best = results[i]
        clusterSpecies = dict((c, []) for c in best.clusters)
        for s in species: clusterSpecies[best.species[s][0]].append(s.id)
        clusterNums = dict((best.clusters[i], i) for i in xrange(len(best.clusters)))
        for c in best.clusters:
            row = [
                i, clusterNums[c], c.speed, 
                ','.join([str(s) for s in clusterSpecies[c]]),
                ','.join(watersheds[c.watersheds == 1])
            ]
            writer.writerow(row)